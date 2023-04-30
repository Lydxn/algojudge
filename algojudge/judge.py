from algojudge.runners import CompileError, RUNNERS
from algojudge.problem import Problem
from typing import NamedTuple

import logging
import traceback


class Submission(NamedTuple):
    id: int
    problem_code: int
    language: str
    source: bytes
    time_limit: int
    memory_limit: int


class Judge:
    def judge(self, submission):
        try:
            problem = Problem(submission.problem_code, submission.time_limit, submission.memory_limit)

            with RUNNERS[submission.language](problem, submission.source) as runner:
                runner.prepare()

                yield 'case-begin', {}
                for case in problem.cases:
                    verdict = runner.run(case)
                    yield 'case-verdict', verdict.to_json()
                yield 'case-end', {}
        except CompileError as e:
            yield 'compile-error', {'error': str(e)}
        except Exception:
            self._report_internal_error(submission)
            yield 'internal-error', {'error': traceback.format_exc()}

    def _report_internal_error(self, submission):
        logging.error(f'Internal error while judging submission {submission.id}.', exc_info=True)
