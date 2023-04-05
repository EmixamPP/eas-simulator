from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scheduler import RunQueue
    from cpu import CPU

class Schedutil:
    def __init__(self, cpus: list[CPU]) -> None:
        self._cpus: list[CPU] = cpus

    def update(self, landscape: dict[CPU, RunQueue]) -> None:
        total_energy: int = 0
        
        for cpu in self._cpus:
            capacity: int = landscape[cpu].cap
            energy: int = 0

            for pstate in cpu.pstates:
                energy = pstate[1]
                cpu.pstate = pstate
                if pstate[0] > capacity:
                    break
            total_energy += energy
