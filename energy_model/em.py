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

    def compute_energy(self, landscape: dict[CPU, int]) -> tuple[float, int]:
        complexity: int = 0
        total_energy: float = 0

        for cpu in self._cpus:
            if cpu in landscape:
                capacity: int = landscape[cpu]
                energy: float = 0

                # assume sorted in increasing order
                for pstate in self._power_table[cpu.type]:
                    energy = (capacity / pstate[0]) * pstate[1]
                    if pstate[0] > capacity:
                        break

                total_energy += energy
                complexity += len(self._power_table[cpu.type])

        return total_energy, complexity
