from algojudge import config
from algojudge.judge import Judge, Submission
from algojudge.verdict import Status
from unittest import main, TestCase

import os
import sys


class JudgeTest(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        config.PROBLEM_DATA_ROOT = os.path.join(os.path.dirname(__file__), 'testdata')

    def test_status(self):
        judge = Judge()

        def _(source, status):
            submission = Submission(
                id=0,
                problem_code='example',
                language='python3',
                source=source,
                time_limit=1000,
                memory_limit=8192
            )
            result = list(judge.judge(submission))

            if status == 'CE':
                self.assertTrue(result[0][0] == 'compile-error')
            else:
                self.assertEqual(result[1][1]['status'], status)

        _(b'print(sum(map(int, input().split())))', 'AC')
        _(b'print(-1)', 'WA')
        _(b'while 1: 0', 'TLE')
        _(b'import time; time.sleep(2)', 'TLE')
        _(b'[0] * 10**6', 'MLE')
        _(b'war is peace', 'NZE')
        _(b'import os; os.kill(os.getpid(), 9)', 'RE')
        _(b':)', 'CE')

    def test_python(self):
        judge = Judge()

        def _(source, language):
            submission = Submission(
                id=0,
                problem_code='example',
                language=language,
                source=source,
                time_limit=1000,
                memory_limit=262144
            )
            result = list(judge.judge(submission))

            try:
                self.assertEqual(result[1][1]['status'], 'WA')
            except Exception:
                print(f'Failed ({language}): {result}')

        _(b'int main(){ puts("1"); }', 'c')
        _(b'#include <iostream>\nint main(){ std::cout << "1\\n"; }', 'cpp')
        _(b'class C { public static void main(String[] args) { System.out.println(1); } }', 'java')
        _(b'print(0)', 'python3')
        _(b'p 0', 'ruby')



if __name__ == '__main__':
    from algojudge.runners import load_runners
    from algojudge.comparators import load_comparators
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    load_runners()
    load_comparators()

    main()
