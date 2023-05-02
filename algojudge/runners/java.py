from algojudge.runners.base import CompiledRunner, CompileError

"""
TODO LIST:
 - use git to separate dev and prod environment
 - add judge ping to make sure when it's actually running
 - rejudge feature for old queued submissions
 - throw an internal error when judge isn't running instead of showing "Queued"
 - add problems to the list
"""

class JavaRunner(CompiledRunner):
    code = 'java'
    source_ext = '.java'
    compiled_ext = '.class'
    max_pids = 32

    def get_compile_args(self):
        return ['/usr/lib/jvm/java-19-openjdk-amd64/bin/javac', self.get_source_filename()]

    def get_execute_args(self):
        return ['/usr/lib/jvm/java-19-openjdk-amd64/bin/java', self.get_compiled_filename()[:-6]]

    def get_source_filename(self):
        return 'Main' + self.source_ext

    def get_compiled_filename(self):
        try:
            return next(self.compile_box.home_path.glob('*.class')).name
        except StopIteration:
            # If an empty file is compiled, no `.class` file will be created yet
            # `javac` won't give any indication of an error.
            raise CompileError('javac did not find a class.')
