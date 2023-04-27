from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cpu import CPU, PerfDom
    from scheduler import LoadGenerator
    from energy_model import EnergyModel

import math

from scheduler import Task, EAS

class EASCorechoiceNextfit(EAS):
    def __init__(self, load_gen: LoadGenerator, cpus: list[CPU], em: EnergyModel, sched_tick_period: int = 1) -> None:
        super().__init__(load_gen, cpus, em, sched_tick_period)
        self._best_cpu_index: dict[PerfDom, int] = {domain: 0 for domain in self._perf_domains_name}
    
    def _find_energy_efficient_cpu(self, by_cpu: CPU, task: Task) -> CPU:
        complexity: int = 0
        
        candidates: list[CPU] = []
        for domain in self._perf_domains_name:
            i: int = self._best_cpu_index[domain]
            init_candidate: CPU = self._cpus_per_domain[domain][i]
            init_candidate_cap: int = self._run_queues[init_candidate].cap

            i = (i+1) % len(self._cpus_per_domain[domain])
            candidate: CPU = self._cpus_per_domain[domain][i]
            candidate_cap: int = self._run_queues[candidate].cap
            complexity += 1
            while init_candidate_cap < candidate_cap:
                i = (i+1) % len(self._cpus_per_domain[domain])
                candidate = self._cpus_per_domain[domain][i]
                candidate_cap = self._run_queues[candidate].cap
                complexity += 1

            candidates.append(candidate)
            self._best_cpu_index[domain] = i

        best_cpu: CPU | None = None
        best_cpu_power: int | float = math.inf
        landscape: dict[CPU, int] = {cpu: self._run_queues[cpu].cap for cpu in candidates}
        for candidate in candidates:
            landscape[candidate] += task.remaining_cycles
            power, em_complexity = self._em.compute_power(landscape)
            landscape[candidate] -= task.remaining_cycles
            if power < best_cpu_power:
                best_cpu = candidate
                best_cpu_power = power
            complexity += em_complexity

        # simulate the energy efficient wake-up balancer
        self._run_queues[by_cpu].insert_kernel_task(Task(100 * complexity, "energy"))

        # assert(best_cpu is not None) was used during dev phase
        return best_cpu