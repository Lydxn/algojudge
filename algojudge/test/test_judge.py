from algojudge import config
from algojudge.judge import Judge, Submission
from algojudge.verdict import Status
from unittest import main, TestCase

import os


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
            header, verdict = next(judge.judge(submission))

            if status == Status.CE:
                self.assertTrue(header == 'compile error')
            else:
                self.assertEqual(verdict.status, status)

        _(b'print(sum(map(int, input().split())))', Status.AC)
        _(b'print(-1)', Status.WA)
        _(b'while 1: 0', Status.TLE)
        _(b'import time; time.sleep(2)', Status.TLE)
        _(b'[0] * 10**6', Status.MLE)
        _(b'war is peace', Status.NZE)
        _(b'import os; os.kill(os.getpid(), 9)', Status.RE)
        _(b':)', Status.CE)


if __name__ == '__main__':
    from algojudge.runners import load_runners
    from algojudge.comparators import load_comparators
    import logging

    logging.basicConfig(
        filename=config.LOG_FILE,
        level=logging.DEBUG,
        format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    load_runners()
    load_comparators()

    main()
