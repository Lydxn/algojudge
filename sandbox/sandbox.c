#define _GNU_SOURCE

#include "cg.h"
#include "fio.h"

#include <errno.h>
#include <fcntl.h>
#include <getopt.h>
#include <grp.h>
#include <limits.h>
#include <sched.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <sys/sysmacros.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define TRACE_PERIOD_US 10000
#define NOBODY 65534

#define BOX_WRITABLE  0x001
#define BOX_DEV       0x002

static const char *optstring = "b:d:Df:Im:p:T:t:R";
static const struct option longopts[] = {
    { "box-name",        1, NULL, 'b' },
    { "box-root",        1, NULL, 'd' },
    { "del",             0, NULL, 'D' },
    { "max-fsize",       1, NULL, 'f' },
    { "init",            0, NULL, 'I' },
    { "memory-limit",    1, NULL, 'm' },
    { "max-pids",        1, NULL, 'p' },
    { "real-time-limit", 1, NULL, 'T' },
    { "cpu-time-limit",  1, NULL, 't' },
    { "run",             0, NULL, 'R' },
    { NULL,              0, NULL,  0 }
};

static char **command;
static char *box_root, box_path[256];
char *box_name;

static uid_t host_uid;
static gid_t host_gid;
static pid_t box_pid, prog_pid;

static int status_pipe[2], fail_pipe[2], fail_write_fd;
static int check_timeout;

static long long cpu_time_limit_ns, real_time_limit_ns;
static int max_fsize_kb;
int memory_limit_kb, max_pids;

/* Triggers upon an error. By convention, exit codes 1 and 2 represent a minor
   and major error, respectively. */
void fail(int exitcode, const char *format, ...) {
    va_list ap; va_start(ap, format);

    // Errors inside the sandbox are not visible from the outside, so we run it
    // through a pipe instead.
    if (fail_write_fd)
        vdprintf(fail_write_fd, format, ap);
    else {
        vfprintf(stderr, format, ap);
        if (box_pid) {
            kill(box_pid, -SIGKILL);
            kill(box_pid, SIGKILL);
        }
    }

    exit(exitcode);
}

/* Parse a single unsigned 32-bit integer, catching any invalid inputs. */
static unsigned uint_parse(const char *str) {
    char *endp;
    long long val = strtoll(str, &endp, 10);
    if (endp && *endp)
        fail(1, "Failed to parse integer: %s\n", str);
    if ((endp && *endp) || val < 0 || val > INT_MAX)
        fail(1, "Integer out of bounds (0 <= val <= %d): %s\n", INT_MAX, str);
    return val;
}

static void populate_box(const char *source, const char *target,
                        const char *fstype, unsigned flags) {
    // Create the directory if it doesn't exist.
    if (mkdir_rec(target, 0755) == -1)
        fail(2, "Failed to populate box with directory '%s': %m\n", target);

    unsigned long mountflags = (!fstype ? MS_BIND | MS_REC : 0);
    if (!(flags & BOX_DEV))
        mountflags |= MS_NODEV;

    if (mount(source, target, fstype, mountflags, NULL) == -1)
        fail(2, "Failed to mount '%s' on '%s': %m\n", source, target);

    if (!(flags & BOX_WRITABLE)) {
        mountflags |= MS_RDONLY;
        if (mount(source, target, fstype, mountflags | MS_REMOUNT, NULL) == -1)
            fail(2, "Failed to remount '%s' on '%s' as read-only: %m\n", source, target);
    }

    // If '/proc' is mounted, make sure to hide the init process from the user.
    if (fstype && !strcmp(fstype, "proc")) {
        if (mount(source, target, fstype, mountflags | MS_REMOUNT, "hidepid=2") == -1)
            fail(2, "Failed to remount '/proc' with 'hidepid=2': %m\n");
    }
}

static void add_device(const char *path, unsigned maj, unsigned min) {
    if (mknod(path, S_IFCHR | 0666, makedev(maj, min)) == -1 && errno != EEXIST)
        fail(2, "Failed to add device '%s': %m\n", path);
}

static void uts_setup() {
    if (sethostname("oj", 2) == -1)
        fail(2, "Failed to set hostname: %m\n");
}

static void io_setup() {
    int newfd;

    #define DUP_FD(fd, name, flags, mode) { \
        if ((newfd = open(name, flags)) == -1) \
            fail(2, "Failed to open() std" name ": %m\n"); \
        if (fchmod(newfd, mode) == -1) \
            fail(2, "Failed to fchmod() std" name ": %\n"); \
        if (dup2(newfd, fd) == -1) \
            fail(2, "Failed to dup() std" name ": %m\n"); \
        if (close(newfd) == -1) \
            fail(2, "Failed to close() std" name ": %m\n"); \
    }

    if (access("in", F_OK) == 0)
        DUP_FD(STDIN_FILENO, "in", O_RDONLY, 0644);
    DUP_FD(STDOUT_FILENO, "out", O_WRONLY | O_CREAT | O_TRUNC, 0622);
    DUP_FD(STDERR_FILENO, "err", O_WRONLY | O_CREAT | O_TRUNC, 0622);
}

static void fs_setup() {
    if (mount(NULL, "/", NULL, MS_PRIVATE | MS_REC, NULL) == -1)
        fail(2, "Failed to mount filesystem as private: %m\n");

    if (mount(box_path, box_path, NULL, MS_BIND | MS_REC, NULL) == -1)
        fail(2, "Failed to bind mount filesystem: %m\n");

    if (chdir(box_path) == -1)
        fail(2, "Failed to change directory: %m\n");

    populate_box("box", "box", NULL, BOX_WRITABLE);
    populate_box("/bin", "bin", NULL, 0);
    populate_box("/lib", "lib", NULL, 0);
    populate_box("/lib64", "lib64", NULL, 0);
    populate_box("/usr/bin", "usr/bin", NULL, 0);
    populate_box("/usr/include", "usr/include", NULL, 0);
    populate_box("/usr/lib", "usr/lib", NULL, 0);
    populate_box(NULL, "proc", "proc", 0);
    populate_box(NULL, "tmp", "tmpfs", BOX_WRITABLE);

    if (mkdir("etc", 0755) == -1 && errno != EEXIST)
        fail(2, "Failed to create '/etc' directory: %m\n");

    // Add 'root' and 'nobody' to the users/groups list.
    if (ezwrite("etc/passwd", "root:x:0:0:root:\nnobody:x:65534:65534:nobody:\n") == -1)
        fail(2, "Failed to write to 'etc/passwd': %m\n");
    if (chmod("etc/passwd", 0644) == -1)
        fail(2, "Failed to set permissions for 'etc/passwd': %m\n");
    if (ezwrite("etc/group", "root:x:0:\nnogroup:x:65534:\n") == -1)
        fail(2, "Failed to write to 'etc/group': %m\n");
    if (chmod("etc/group", 0644) == -1)
        fail(2, "Failed to set permissions for 'etc/group'");

    if (mkdir("dev", 0755) == -1 && errno != EEXIST)
        fail(2, "Failed to create '/dev' directory: %m\n");

    add_device("dev/null", 1, 3);
    add_device("dev/random", 1, 8);
    add_device("dev/urandom", 1, 9);
    add_device("dev/zero", 1, 5);

    /* Magically place ourselves inside. */

    if (mkdir("put_old", 0777) == -1)
        fail(2, "Failed to create 'put_old' directory: %m\n");
    if (syscall(SYS_pivot_root, ".", "put_old") == -1)
        fail(2, "Failed to pivot root: %m\n");
    if (chdir("/") == -1)
        fail(2, "Failed to switch to root\n");
    if (umount2("put_old", MNT_DETACH) == -1)
        fail(2, "Failed to unmount 'put_old' directory: %m\n");
    if (rmdir("put_old") == -1)
        fail(2, "Failed to remove 'put_old' directory: %m\n");
}

static void rlim_setup() {
    if (max_fsize_kb) {
        struct rlimit rl = { max_fsize_kb << 10, max_fsize_kb << 10 };
        setrlimit(RLIMIT_FSIZE, &rl);
    }
}

static void user_setup() {
    // Switch ourselves to an unpriviliged user (a.k.a. nobody).
    if (setresgid(NOBODY, NOBODY, NOBODY) == -1)
        fail(2, "setresgid(): %m\n");
    if (setgroups(0, NULL) == -1)
        fail(2, "setgroups(): %m\n");
    if (setresuid(NOBODY, NOBODY, NOBODY) == -1)
        fail(2, "setresuid(): %m\n");
}

static void run_program() {
    cg_setup();
    fs_setup();
    uts_setup();
    io_setup();
    rlim_setup();
    user_setup();

    if (chdir("home") == -1)
        fail(2, "Failed to chdir() to /home directory: %m\n");

    char *envp[] = {"PATH=/bin:/usr/bin", NULL};
    if (execve(command[0], command, envp) == -1)
        fail(2, "execve('%s'): %m\n", command[0]);

    _exit(1);
}

static void run_box() {
    if ((prog_pid = fork()) == -1)
        fail(2, "fork(): %m\n");

    if (prog_pid == 0)
        run_program();

    int status;
    if (waitpid(prog_pid, &status, 0) == -1)
        fail(2, "waitpid(): %m\n");

    if (write(status_pipe[1], &status, sizeof(status)) == -1)
        fail(2, "Failed to write to status pipe: %m\n");

    _exit(0);
}

struct timespec start, end;

static long long get_real_time() {
    clock_gettime(CLOCK_MONOTONIC, &end);
    return 1000000000LL * (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec);
}

static void trace_handler(int sig) {
    check_timeout = 1;
}

/* Traces the child process until termination and records its results. */
static void trace() {
    struct sigaction sa = { 0 };
    sa.sa_handler = trace_handler;
    sigaction(SIGALRM, &sa, NULL);

    struct itimerval it;
    it.it_interval.tv_sec = it.it_value.tv_sec = 0;
    it.it_interval.tv_usec = it.it_value.tv_usec = TRACE_PERIOD_US;
    setitimer(ITIMER_REAL, &it, NULL);

    struct rusage ru; int status;
    int timeout = 0;

    // Starting the clock now could happen before the child runs. However, the
    // difference is negligible, and real time isn't too important to us anyway.
    clock_gettime(CLOCK_MONOTONIC, &start);

    while (1) {
        if (check_timeout) {
            if ( (cpu_time_limit_ns && cg_cpu_time() > cpu_time_limit_ns) ||
                 (real_time_limit_ns && get_real_time() > real_time_limit_ns) ) {
                timeout = 1;
                break;
            }
            check_timeout = 0;
        }

        pid_t pid = wait4(box_pid, &status, 0, &ru);
        if (pid != -1)
            break;
        if (errno != EINTR)
            fail(2, "wait4(): %m\n");
    }

    // Report any errors that occured inside the sandbox.
    char buf[1024]; int len;
    if ((len = read(fail_pipe[0], &buf, sizeof(buf))) > 0) {
        buf[len] = '\0';
        fail(2, buf);
    }

    // The program could have terminated or timed out. Either way, we must kill it.
    kill(box_pid, SIGKILL);

    int exitcode = -1, signal = -1;

    if (!timeout) {
        read(status_pipe[0], &status, sizeof(status));
        if (WIFEXITED(status))
            exitcode = WEXITSTATUS(status);
        else if (WIFSIGNALED(status))
            signal = WTERMSIG(status);
        else if (WIFSTOPPED(status))
            signal = WSTOPSIG(status);
        else
            fail(2, "Sandbox received bad status %d\n");
    }

    printf("cpu_time_ns: %lld\n", cg_cpu_time());
    printf("real_time_ns: %lld\n", get_real_time());
    printf("memory_kb: %d\n", cg_memory_usage());
    printf("timeout: %d\n", timeout);
    printf("oom_kill: %d\n", cg_oom_kill());
    printf("exitcode: %d\n", exitcode);
    printf("signal: %d\n", signal);
}

/* Initializes the sandbox at the given path. */
static void init() {
    if (mkdir(box_path, 0755) == -1) {
        if (errno == EEXIST)
            fail(2, "Box '%s' already exists.\n", box_name);
        else
            fail(2, "Failed to initialize box: %m\n");
    }

    chdir(box_path);

    // Create a writable directory where the user will reside.
    if (mkdir("home", 0777) == -1)
        fail(2, "Failed to create '/home' directory: %m\n");
    if (chmod("home", 0777) == -1)
        fail(2, "Failed to chown() '/home' directory: %m\n");

    cg_init(box_name);

    printf("Sandbox was successfully initialized!\n");
}

/* Deletes the sandbox, along with everything inside it. */
static void delete() {
    if (rmdir_rec(box_path) == -1)
        fail(2, "Failed to delete box: %m\n");

    cg_delete();

    printf("Sandbox was successfully deleted!\n");
}

/* Runs the program inside the sandbox. */
static void run() {
    if (access(box_path, F_OK) != 0)
        fail(2, "This sandbox has not been initialized yet; please run with --init first.\n");
    host_uid = getuid(), host_gid = getgid();

    // Ensure that all files in the sandbox are owned by root.
    if (chown_rec(box_path, host_uid, host_gid) == -1)
        fail(2, "Failed to chown() box: %m\n");

    // Create a pipe to record the exitcode/signal of the running process.
    if (pipe(status_pipe) == -1)
        fail(2, "Failed to create status pipe: %m\n");

    // Create another pipe to listen for failures.
    if (pipe(fail_pipe) == -1)
        fail(2, "Failed to create fail pipe: %m\n");

    box_pid = syscall(
        SYS_clone,
        CLONE_NEWIPC | CLONE_NEWNET | CLONE_NEWNS | CLONE_NEWPID | CLONE_NEWUTS | SIGCHLD,
        0, 0, 0, 0);

    if (box_pid == -1)
        fail(2, "sys_clone(): %m\n");

    if (box_pid == 0) {
        fail_write_fd = fail_pipe[1];
        close(status_pipe[0]); close(fail_pipe[0]);

        run_box();
        return;
    }

    close(fail_pipe[1]); close(fail_pipe[1]);
    trace();
}

int main(int argc, char *argv[]) {
    if (getuid() != 0 || getgid() != 0)
        fail(1, "You must run this program as root.\n");

    int opt, mode = 0;

    while ((opt = getopt_long(argc, argv, optstring, longopts, NULL)) != -1) {
        switch (opt) {
        case 'D':
        case 'I':
        case 'R':
            if (mode)
                fail(1, "Please specify a single mode (-D/-I/-R).\n");
            mode = opt;
            break;
        case 'b':
            box_name = optarg;
            break;
        case 'd':
            box_root = optarg;
            break;
        case 'f':
            max_fsize_kb = uint_parse(optarg);
            break;
        case 'm':
            memory_limit_kb = uint_parse(optarg);
            break;
        case 'p':
            max_pids = uint_parse(optarg);
            break;
        case 'T':
            real_time_limit_ns = 1000000LL * uint_parse(optarg);
            break;
        case 't':
            cpu_time_limit_ns = 1000000LL * uint_parse(optarg);
            break;
        }
    }

    snprintf(box_path, sizeof(box_path), "%s/%s", box_root, box_name);

    switch (mode) {
    case 'D':
        delete();
        break;
    case 'I':
        init();
        break;
    case 'R':
        command = argv + optind;
        run();
        break;
    }

    return 0;
}
