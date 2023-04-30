from enum import IntFlag, auto


class Status(IntFlag):
    AC = 0
    WA = auto()
    TLE = auto()
    MLE = auto()
    NZE = auto()
    RE = auto()
    CE = auto()
    IE = auto()
    Q = auto()
    J = auto()


class Verdict:
    def __init__(
        self,
        case,
        status,
        message=None,
        cpu_time=None,
        real_time=None,
        memory=None
    ):
        self.case = case
        self.status = status
        self.message = message
        self.cpu_time = cpu_time
        self.real_time = real_time
        self.memory = memory

    def to_json(self):
        return {
            'case-num': self.case.num,
            'input': self.case.infile,
            'output': self.case.outfile,
            'status': self.status.name,
            'message': self.message,
            'cpu-time': self.cpu_time,
            'real-time': self.real_time,
            'memory': self.memory
        }
