from typing import NewType

from scheduler import Task
from profiler import Profiler


PerfDom = NewType('PerfDom', str)
# (capacity, power, frequency)
PState = NewType('PState', tuple[int, int, int])


class CPU:
    def __init__(self, perf_domain: PerfDom, pstates: list[PState], capacity: int) -> None:
        # assume sorted in increasing order
        self.pstates: list[PState] = pstates
        self._perf_domain: PerfDom = perf_domain
        # maximum number of instructions executed by sec
        self._max_capacity: int = capacity
        self._frequency: int = pstates[0][2]

    @property
    def frequency(self) -> int:
        return self._frequency

    @frequency.setter
    def frequency(self, pstate: PState) -> None:
        assert(pstate in self.pstates)
        self._frequency = pstate[2]

    @property
    def type(self) -> PerfDom:
        return self._perf_domain

    def execute_for(self, task: Task, time_ns: int) -> None:
        cycles = time_ns * 10**9 * self._frequency
        task.execute(cycles)
        Profiler.executed_for_on(task, cycles, self)

    @property
    def max_capacity(self) -> int:
        return self._max_capacity
