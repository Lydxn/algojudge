from algojudge.runners.base import CompileError, Runner
from importlib import import_module

import os


RUNNERS = Runner._registry

def load_runners():
    for module in os.listdir(os.path.dirname(__file__)):
        if module.endswith('.py') and module != '__init__.py':
            import_module(f'algojudge.runners.{module[:-3]}')
