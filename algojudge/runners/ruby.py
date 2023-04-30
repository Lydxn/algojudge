from algojudge.runners.base import Runner


class RubyRunner(Runner):
    code = 'ruby'
    source_ext = '.rb'

    def get_execute_args(self):
        return ['/usr/bin/ruby', self.get_source_filename()]
