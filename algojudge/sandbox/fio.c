#define _GNU_SOURCE

#include "fio.h"

#include <errno.h>
#include <ftw.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <unistd.h>

/* Create a directory in the given path recursively. */
int mkdir_rec(const char *path, mode_t mode) {
    char buf[256];
    snprintf(buf, sizeof(buf), "%s", path);
    for (char *ptr = buf + 1; *ptr; ptr++) {
        if (*ptr == '/') {
            *ptr = '\0';
            if (mkdir(buf, mode) == -1 && errno != EEXIST)
                return -1;
            *ptr = '/';
        }
    }
    if (mkdir(path, mode) == -1 && errno != EEXIST)
        return -1;
    return 0;
}

static int rmdir_fn(const char *fpath, const struct stat *sb, int typeflag, struct FTW *ftwbuf) {
    return remove(fpath);
}

/* Delete all files in the path recursively. */
int rmdir_rec(const char *path) {
    return nftw(path, rmdir_fn, 20, FTW_DEPTH | FTW_MOUNT | FTW_PHYS);
}

static int chown_uid, chown_gid;

static int chown_fn(const char *fpath, const struct stat *sb, int typeflag, struct FTW *ftwbuf) {
    return chown(fpath, chown_uid, chown_gid);
}

/* Change ownership of files in the path recursively. */
int chown_rec(const char *path, uid_t uid, gid_t gid) {
    chown_uid = uid, chown_gid = gid;
    return nftw(path, chown_fn, 20, FTW_DEPTH | FTW_MOUNT | FTW_PHYS);
}

/* Similar to `fprintf` but takes a path instead of a stream. */
int ezwrite(const char *path, const char *format, ...) {
    va_list ap; va_start(ap, format);
    return vezwrite(path, format, ap);
}

int vezwrite(const char *path, const char *format, va_list ap) {
    int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC);
    if (fd == -1)
        return -1;

    char buf[1024];

    int len = vsnprintf(buf, sizeof(buf), format, ap);
    if (write(fd, buf, len) == -1)
        return -1;

    if (close(fd) == -1)
        return -1;

    return len;
}
