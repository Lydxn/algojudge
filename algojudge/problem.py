from algojudge import config
from pathlib import Path
from typing import NamedTuple
from zipfile import ZipFile

import yaml


class TestCase(NamedTuple):
    num: int
    infile: str
    outfile: str
    time_limit: int
    memory_limit: int


class Problem:
    def __init__(self, code, time_limit, memory_limit):
        self.code = code
        self.time_limit = time_limit
        self.memory_limit = memory_limit

        self.problem_path = Path(config.PROBLEM_DATA_ROOT) / self.code

        with open(self.problem_path / 'config.yml') as f:
            data = yaml.safe_load(f)
            self.archive_name = data['archive']
            self.comparator = data.get('checker', 'standard')
            self.cases = self._parse_cases(data)

    def open_archive(self):
        return ZipFile(self.problem_path / self.archive_name, 'r')

    def _parse_cases(self, data):
        cases = []
        for index, case in enumerate(data['cases']):
            cases.append(TestCase(index + 1, case['in'], case['out'],
                                  self.time_limit, self.memory_limit))
        return cases
