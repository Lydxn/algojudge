from importlib import import_module

import os


COMPARATORS = {}

def load_comparators():
    for module in os.listdir(os.path.dirname(__file__)):
        if module.endswith('.py') and module != '__init__.py':
            import_module(f'algojudge.comparators.{module[:-3]}')

def comparator(name):
    def wrapper(func):
        COMPARATORS[name] = func
    return wrapper
