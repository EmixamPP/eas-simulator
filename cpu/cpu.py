from __future__ import annotations
from typing import TYPE_CHECKING, NewType, Any
if TYPE_CHECKING:
    from profiler import Profiler

import math

from scheduler import Task

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

        # maximum number of instructions executed by sec
        self._max_capacity: int = pstates[-1][0]

    def start(self, profiler: Profiler):
        self._pstate: PState = self.pstates[0]
        self.profiler: Profiler = profiler
        profiler.update_power_consumption(self.pstate[1], self.name)
        
    @property
    def pstate(self) -> PState:
        return self._pstate

    @pstate.setter
    def pstate(self, pstate: PState) -> None:
        #assert(pstate in self.pstates) was used during dev phase
        self.profiler.update_power_consumption(pstate[1], self.name)
        self._pstate = pstate

    @property
    def type(self) -> PerfDom:
        return self._perf_domain

    def execute_for(self, task: Task, time_ms: int) -> None:
        cycles: int = math.ceil(self.pstate[0] * time_ms * 10**-3)

        remaining_cycles = task.remaining_cycles

        try:
            task.execute(cycles)
        except AssertionError:
            self.profiler.executed_for(task.name, remaining_cycles)
            self.profiler.executed_for("slack", cycles - remaining_cycles)
        else:
            self.profiler.executed_for(task.name, cycles)

    @property
    def max_capacity(self) -> int:
        return self._max_capacity
