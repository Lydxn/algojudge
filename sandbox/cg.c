#include "cg.h"
#include "fio.h"
#include "sandbox.h"

#include <fcntl.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static const char *CG_CONTROLLERS[] = { "cpuacct", "memory", "pids" };

static void cg_getpath(char *buf, size_t size, size_t controller, const char *path) {
    snprintf(buf, size, "/sys/fs/cgroup/%s/sandbox/%s/%s",
             CG_CONTROLLERS[controller], box_name, path ? path : "");
}

void cg_read(char *buf, size_t count, size_t controller, const char *filename) {
    char path[256];
    cg_getpath(path, sizeof(path), controller, filename);

    int fd = open(path, O_RDONLY);
    if (fd == -1)
        fail(2, "Failed to open '%s' for reading: %m\n", path);

    int nbytes;
    if ((nbytes = read(fd, buf, count)) == -1)
        fail(2, "Failed to read '%s': %m\n", path);
    if (nbytes == count)
        fail(2, "File '%s' too long to read.\n");

    // Remove any trailing newlines at the end of the file.
    while (nbytes > 0 && buf[nbytes - 1] == '\n') --nbytes;

    buf[nbytes] = '\0';

    if (close(fd) == -1)
        fail(2, "Failed to close '%s' after reading: %m\n", path);
}

void cg_write(size_t controller, const char *filename, const char *format, ...) {
    va_list ap; va_start(ap, format);

    char path[256];
    cg_getpath(path, sizeof(path), controller, filename);

    if (vezwrite(path, format, ap) == -1)
        fail(2, "Failed to write to '%s': %m\n", path);
}

/* Returns the total cpu time of the process, in nanoseconds. */
long long cg_cpu_time() {
    char buf[256];
    cg_read(buf, sizeof(buf), CG_CPUACCT, "cpuacct.usage");
    return atoll(buf);
}

/* Returns the maximum memory usage of the process, in kilobytes. */
int cg_memory_usage() {
    char buf[256];
    cg_read(buf, sizeof(buf), CG_MEMORY, "memory.memsw.max_usage_in_bytes");
    unsigned long long memsw = atoll(buf);

    return memsw >> 10;
}

/* Returns 1 if the system ran out of memory, and 0 otherwise. */
int cg_oom_kill() {
    char buf[256];
    cg_read(buf, sizeof(buf), CG_MEMORY, "memory.oom_control");

    int oom_kill = 0;
    for (char *ptr = buf; *ptr; ptr = strchr(ptr, '\n') + 1)
        if (sscanf(ptr, "oom_kill %d", &oom_kill) == 1)
            break;
    return oom_kill;
}

void cg_setup() {
    pid_t pid = getpid();

    if (max_pids) {
        cg_write(CG_PIDS, "tasks", "%d\n", pid);
        cg_write(CG_PIDS, "pids.max", "%d\n", max_pids);
    }

    if (memory_limit_kb) {
        cg_write(CG_MEMORY, "tasks", "%d\n", pid);
        cg_write(CG_MEMORY, "memory.limit_in_bytes", "%lld\n", (long long) memory_limit_kb << 10);
        cg_write(CG_MEMORY, "memory.memsw.limit_in_bytes", "%lld\n", (long long) memory_limit_kb << 10);
    }

    cg_write(CG_CPUACCT, "tasks", "%d\n", pid);
    cg_write(CG_CPUACCT, "cpuacct.usage", "0\n");
}

void cg_init() {
    char path[256];
    for (int controller = 0; controller < sizeof(CG_CONTROLLERS) / sizeof(char*); controller++) {
        cg_getpath(path, sizeof(path), controller, NULL);
        if (mkdir_rec(path, 0755) == -1)
            fail(2, "Failed to create cgroup directory at '%s': %m\n", path);
    }
}

void cg_delete() {
    char path[256];
    for (int controller = 0; controller < sizeof(CG_CONTROLLERS) / sizeof(char*); controller++) {
        cg_getpath(path, sizeof(path), controller, NULL);
        if (rmdir(path) == -1)
            fail(2, "Failed to delete cgroup directory at '%s': %m\n", path);
    }
}
