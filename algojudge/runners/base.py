from algojudge import config, utils
from algojudge.comparators import COMPARATORS
from algojudge.sandbox import Sandbox, SandboxConfig
from algojudge.verdict import Status, Verdict
from abc import ABCMeta, abstractmethod

import os
import uuid


class CompileError(Exception):
    def __init__(self, message):
        if isinstance(message, str):
            super().__init__(message)
        else:
            super().__init__(message.decode('utf-8', errors='replace'))


class Runner(metaclass=ABCMeta):
    name: str
    code: str
    source_ext: str
    max_fsize: int = 262144
    max_pids: int = 1

    _registry = {}

    def __init__(self, problem, source):
        self.problem = problem
        # Convert all line endings in source to `\n` and enforce UTF-8 encoding.
        self.source = utils.normalize_lines(source).decode('utf-8', errors='replace')

    def __enter__(self):
        self.problem_archive = self.problem.open_archive()
        return self

    def __init_subclass__(cls, register=True, **kwargs):
        super().__init_subclass__(**kwargs)
        if register:
            cls._registry[cls.code] = cls

    def prepare(self):
        pass

    def run(self, case):
        # The sandbox is given a randomly-generated uuid name; the chance that
        # a duplicate occurs is so incredibly low that we should be fine leaving
        # it alone... probably.
        with Sandbox(f'box-{uuid.uuid4().hex}') as self.box:
            self.copy_executable()

            # Copy the case input from the archive into the sandbox directory.
            old_name = self.problem_archive.extract(case.infile, self.box.root_path)
            os.rename(old_name, self.box.stdin_path)

            config = SandboxConfig(
                cpu_time_limit=case.time_limit,
                # Real-time isn't really an accurate representation of execution
                # time, rather a security measure just to make sure that the
                # program can't sleep() forever.
                real_time_limit=case.time_limit*2,
                memory_limit=case.memory_limit,
                max_fsize=self.max_fsize,
                max_pids=self.max_pids
            )

            result = self.box.run(self.get_execute_args(), config)

            verdict = Verdict(
                case=case,
                status=Status.J,
                message='',
                cpu_time=result.cpu_time_ns,
                real_time=result.real_time_ns,
                memory=result.memory_kb
            )

            if result.is_tle():
                verdict.status = Status.TLE
                verdict.cpu_time = verdict.wall_time = None
            elif result.is_mle():
                verdict.status = Status.MLE
                verdict.memory = None
            elif result.is_re():
                verdict.status = Status.RE
                verdict.message = f'signal {result.signal}'
            elif result.is_nze():
                verdict.status = Status.NZE
                verdict.message = f'exitcode {result.exitcode}'
            else:
                compare = COMPARATORS[self.problem.comparator]
                with open(self.box.stdout_path, 'rb') as fa, self.problem_archive.open(case.outfile, 'r') as fb:
                    verdict.status = (Status.WA, Status.AC)[compare(fa, fb)]

            return verdict

    def copy_executable(self):
        # Copy the source code into the sandbox directory.
        with open(self.box.home_path / self.get_source_filename(), 'w') as f:
            f.write(self.source)

    def get_source_filename(self):
        return 'main' + self.source_ext

    def __exit__(self, exc_type, exc_value, traceback):
        self.problem_archive.close()

    @abstractmethod
    def get_execute_args(self):
        pass


class CompiledRunner(Runner, register=False):
    compiled_ext: str

    def __init__(self, problem, source):
        super().__init__(problem, source)

    def __enter__(self):
        super().__enter__()

        self.compile_box = Sandbox(f'cbox-{uuid.uuid4().hex}')
        self.compile_box.__enter__()

        return self

    def prepare(self):
        # Copy the source code into the sandbox directory to be compiled.
        with open(self.compile_box.home_path / self.get_source_filename(), 'w') as f:
            f.write(self.source)

        # We must run the compilation step separately in case the compiler
        # decides to bug out on us or cause a compiler bomb.
        self.compiled_result = self.compile_box.run(self.get_compile_args(), config.SANDBOX_COMPILE_CONFIG)

        if self.compiled_result.is_tle():
            raise CompileError('compilation took too long :(')
        if self.compilation_failed():
            raise CompileError(self.get_compile_output())

    def copy_executable(self):
        # Copy the binary into the sandbox directory.
        utils.copy(self.compile_box.home_path / self.get_compiled_filename(),
                   self.box.home_path / self.get_compiled_filename())

    def compilation_failed(self):
        return self.compiled_result.exitcode != 0

    def get_compile_output(self):
        return self.compile_box.stderr()

    def get_compiled_filename(self):
        return 'main' + self.compiled_ext

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        self.compile_box.__exit__(exc_type, exc_value, traceback)

    @abstractmethod
    def get_compile_args(self):
        pass
