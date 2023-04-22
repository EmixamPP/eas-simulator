from typing import NewType, Any
import math

from scheduler import Task
from profiler import Profiler

PerfDom = NewType('PerfDom', str)
PState = NewType('PState', tuple[int, int])  # (capacity, power)


class CPU:
    # One CPU == Many Cores == Many Logical CPUs
    # One Core == One Logical CPU

    def __init__(self, perf_domain: PerfDom, pstates: list[PState], name: Any) -> None:
        self.name: Any = name
        # assume sorted in increasing order
        self.pstates: list[PState] = pstates
        self._perf_domain: PerfDom = perf_domain

        self._pstate: PState = pstates[0]
        self._time_ms: int = 0  # should reflect the actual execution time of EAS
        Profiler.update_power_consumption(self.pstate[1], 0, self.name)

        # maximum number of instructions executed by sec
        self._max_capacity: int = self.pstate[0]

    def restart(self):
        self._pstate = self.pstates[0]
        self._time_ms = 0
        Profiler.update_power_consumption(self.pstate[1], 0, self.name)

    @property
    def pstate(self) -> PState:
        return self._pstate

    @pstate.setter
    def pstate(self, pstate: PState) -> None:
        assert(pstate in self.pstates)
        Profiler.update_power_consumption(pstate[1], self._time_ms, self.name)
        self._pstate = pstate

    @property
    def type(self) -> PerfDom:
        return self._perf_domain

    def execute_for(self, task: Task, time_ms: int) -> None:
        cycles: int = math.ceil(self.pstate[0] * time_ms * 10**-3)

        remaining_cycles = task.remaining_cycles
        self._time_ms += time_ms

        try:
            task.execute(cycles)
        except AssertionError:
            Profiler.executed_for(task.name, remaining_cycles)
            Profiler.executed_for("slack", cycles - remaining_cycles)
        else:
            Profiler.executed_for(task.name, cycles)

    @property
    def max_capacity(self) -> int:
        return self._max_capacity
