#ifndef FIO_H
#define FIO_H

#include <stdarg.h>
#include <sys/stat.h>

int mkdir_rec(const char *path, mode_t mode);
int chown_rec(const char *path, uid_t uid, gid_t gid);
int rmdir_rec(const char *path);

int ezwrite(const char *filename, const char *format, ...);
int vezwrite(const char *filename, const char *format, va_list ap);

#endif  // FIO_H
