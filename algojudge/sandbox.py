import os
from pathlib import Path
from shutil import rmtree
from subprocess import Popen, PIPE

BOX_BASEDIR = os.environ['BOX_BASEDIR']


class SandboxResult:
    def __init__(self, cpu_time_ns, real_time_ns, memory_kb, timeout, oom_kill, exitcode, signal):
        self.cpu_time_ns = cpu_time_ns
        self.real_time_ns = real_time_ns
        self.memory_kb = memory_kb
        self.timeout = bool(timeout)
        self.oom_kill = bool(oom_kill)
        self.exitcode = None if exitcode == -1 else exitcode
        self.signal = None if signal == -1 else signal

    def is_mle(self):
        return self.oom_kill

    def is_tle(self):
        return self.timeout

    def is_nze(self):
        return self.exitcode != 0 and self.exitcode is not None

    def is_re(self):
        return self.signal is not None


class SandboxError(Exception):
    def __init__(self, message):
        if isinstance(message, str):
            super().__init__(message)
        else:
            super().__init__(message.decode('utf-8', errors='replace'))


class SandboxConfig:
    def __init__(self, cpu_time_limit=None, real_time_limit=None,
                 memory_limit=None, max_fsize=262144, max_pids=1):
        self.cpu_time_limit = cpu_time_limit
        self.real_time_limit = real_time_limit
        self.memory_limit = memory_limit
        self.max_fsize = max_fsize
        self.max_pids = max_pids

    def get_opts(self):
        args = []

        if self.cpu_time_limit is not None:
            args += [f'--cpu-time-limit={self.cpu_time_limit}']
        if self.real_time_limit is not None:
            args += [f'--real-time-limit={self.real_time_limit}']
        if self.memory_limit is not None:
            args += [f'--memory-limit={self.memory_limit}']
        if self.max_fsize is not None:
            args += [f'--max-fsize={self.max_fsize}']
        if self.max_pids is not None:
            args += [f'--max-pids={self.max_pids}']

        return args


class Sandbox:
    """A simple Python interface to the sandbox written in C."""

    def __init__(self, box_name):
        self.box_name = Path(box_name)

        self.root_path = BOX_BASEDIR / self.box_name

        self.home_path = self.root_path / 'home'
        self.stdin_path = self.root_path / 'in'
        self.stdout_path = self.root_path / 'out'
        self.stderr_path = self.root_path / 'err'

    def __enter__(self):
        proc = Popen(['sandbox', f'--box-name={self.box_name}', '--init'], stdout=PIPE, stderr=PIPE)
        _, stderr = proc.communicate()

        if proc.returncode > 0:
            raise SandboxError(stderr.decode())

        return self

    def run(self, command, config):
        proc = Popen(['sandbox', f'--box-name={self.box_name}', '--run', *config.get_opts(), '--', *command],
                     stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()

        if proc.returncode != 0:
            raise SandboxError(stderr.decode())

        result = {}
        for line in stdout.rstrip().decode().split('\n'):
            key, value = line.split(': ')
            result[key] = int(value)

        return SandboxResult(**result)

    def stdout(self):
        with open(self.stdout_path, 'rb') as f:
            return f.read()

    def stderr(self):
        with open(self.stderr_path, 'rb') as f:
            return f.read()

    def __exit__(self, exc_type, exc_value, traceback):
        proc = Popen(['sandbox', f'--box-name={self.box_name}', '--del'], stdout=PIPE, stderr=PIPE)
        _, stderr = proc.communicate()

        if proc.returncode != 0:
            raise SandboxError(stderr.decode())
