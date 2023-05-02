#ifndef CG_H
#define CG_H

#include <stddef.h>

#define CG_CPUACCT    0
#define CG_MEMORY     1
#define CG_PIDS       2

void cg_read(char *buf, size_t count, size_t controller, const char *filename);
void cg_write(size_t controller, const char *filename, const char *format, ...);

long long cg_cpu_time();
int cg_memory_usage();
int cg_oom_kill();

void cg_setup();
void cg_init();
void cg_delete();

#endif  // CG_H
