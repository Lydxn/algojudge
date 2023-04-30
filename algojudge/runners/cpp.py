from algojudge.runners.base import CompiledRunner


class CPPRunner(CompiledRunner):
    code = 'cpp'
    source_ext = '.cpp'
    compiled_ext = ''

    def get_compile_args(self):
        return [
            '/usr/bin/g++',
            '-O2',
            '-Wall',
            '-std=c++17',
            '-o', self.get_compiled_filename(),
            self.get_source_filename(),
            '-lm'
        ]

    def get_execute_args(self):
        return [self.get_compiled_filename()]
