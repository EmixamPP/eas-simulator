from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cpu import CPU, PerfDom, PState


class EnergyModel:
    def __init__(self, cpus: list[CPU]) -> None:
        self._power_table: dict[PerfDom, list[PState]] = {}
        self._cpus: list[CPU] = cpus

        for cpu in cpus:
            self._power_table[cpu.type] = cpu.pstates

    def compute_power(self, landscape: dict[CPU, int]) -> tuple[int, int]:
        complexity: int = 0
        total_power: int = 0

        for cpu in self._cpus:
            if cpu in landscape:
                capacity: int = landscape[cpu]
                power: int = 0

                # assume sorted in increasing order
                for pstate in self._power_table[cpu.type]:
                    power = pstate[1]
                    if pstate[0] > capacity:
                        break

                total_power += power
                complexity += len(self._power_table[cpu.type])

        return total_power, complexity
