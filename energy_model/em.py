from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cpu import CPU, PerfDom, PState


class EnergyModel:
    def __init__(self, cpus: list[CPU]) -> None:
        self._power_table: dict[PerfDom, list[PState]] = {}
        self.perf_domains_name: list[PerfDom] = []
        self._cpus: list[CPU] = cpus

        for cpu in cpus:
            perf_domain_name = cpu.type
            if perf_domain_name not in self.perf_domains_name:
                self.perf_domains_name.append(perf_domain_name)
                self._power_table[perf_domain_name] = cpu.pstates

    def compute_energy(self, landscape: dict[CPU, int]) -> tuple[int, int]:
        used_cycle: int = 0
        total_energy: int = 0

        for cpu in self._cpus:
            capacity: int = landscape[cpu]
            energy: int = 0

            # assume sorted in increasing order
            for pstate in self._power_table[cpu.type]:
                energy = pstate[1]
                used_cycle += 1
                if pstate[0] > capacity:
                    break

            total_energy += energy
            used_cycle += 1

        return total_energy, used_cycle
