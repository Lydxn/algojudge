#ifndef SANDBOX_H
#define SANDBOX_H

extern char *box_name;
extern int memory_limit_kb, max_pids;

void fail(int exitcode, const char *format, ...);

#endif  // SANDBOX_H
