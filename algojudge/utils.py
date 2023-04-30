from shutil import copy2

import os


# Copy a file from one location to another while preserving the file's metadata.
def copy(src, dst):
    copy2(src, dst)
    st = os.stat(src)
    os.chown(dst, st.st_uid, st.st_gid)


# Normalize text with UNIX-style line endings (`\n`).
def normalize_lines(text):
    return text.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
