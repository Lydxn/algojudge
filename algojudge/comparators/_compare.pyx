cdef class BufferedReader:
    cdef fobj
    cdef bytes buf
    cdef int ip, iend

    def __init__(self, fobj):
        self.fobj = fobj
        self.ip = self.iend = 0

    cdef int getchar(self):
        if self.ip == self.iend:
            self.buf = self.fobj.read(65536)
            if not self.buf:
                return -1
            self.iend = len(self.buf)
            self.ip = 0
        cdef int ch = self.buf[self.ip]
        self.ip += 1
        return ch

cdef int isspace(c):
    return c == 9 or c == 32

def compare_identical(fa, fb):
    cdef BufferedReader ra = BufferedReader(fa)
    cdef BufferedReader rb = BufferedReader(fb)

    while True:
        a = ra.getchar()
        b = rb.getchar()
        if a != b:
            return False
        if a == -1:
            return True

# Checks whether two streams are "eye-identical". In other words, whether they
# are indistinguishable in an editor which does not show trailing whitespace.
# Non-UNIX newlines such as `\r\n` or `\r` are not supported.
def compare_standard(fa, fb):
    cdef BufferedReader ra = BufferedReader(fa)
    cdef BufferedReader rb = BufferedReader(fb)
    cdef int a, b, sa, sb

    while True:
        a = ra.getchar()
        b = rb.getchar()

        # Continue reading each stream until we hit a non-space character,
        # keeping track of the number of consecutive spaces read.
        sa = sb = 0
        while isspace(a):
            a = ra.getchar()
            sa += 1
        while isspace(b):
            b = rb.getchar()
            sb += 1

        # If one stream reaches EOF, so should the other stream, minus
        # any trailing whitspace.
        if a == -1:
            while isspace(b) or b == 10:
                b = rb.getchar()
            return b == -1
        if b == -1:
            while isspace(a) or a == 10:
                a = ra.getchar()
            return a == -1

        # After skipping the spaces, the next pair of bytes must be
        # identical. Also, the number of spaces skipped must be the same for
        # both streams. The only exception to this rule is if both bytes are
        # newlines, which is OK because trailing whitespace doesn't matter.
        if a != b or (sa != sb and a != 10):
            return False

    return True
