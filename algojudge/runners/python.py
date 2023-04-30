from algojudge.runners.base import CompiledRunner


class Python3Runner(CompiledRunner):
    code = 'python3'
    source_ext = '.py'
    compiled_ext = '.pyc'

    def get_compile_output(self):
        return self.compile_box.stdout()

    def get_compile_args(self):
        return [
            '/usr/bin/python3',
            '-m', 'compileall',
            '-b', self.get_source_filename()
        ]

    def get_execute_args(self):
        return ['/usr/bin/python3', self.get_compiled_filename()]
