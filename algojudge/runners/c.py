from algojudge.runners.base import CompiledRunner


class CRunner(CompiledRunner):
    code = 'c'
    source_ext = '.c'
    compiled_ext = ''

    def get_compile_args(self):
        return [
            '/usr/bin/gcc',
            '-O2',
            '-Wall',
            '-std=c99',
            '-o', self.get_compiled_filename(),
            self.get_source_filename(),
            '-lm'
        ]

    def get_execute_args(self):
        return [self.get_compiled_filename()]
