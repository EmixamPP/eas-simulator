from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cpu import CPU
    from scheduler import LoadGenerator
    from energy_model import EnergyModel, Schedutil

import math

from scheduler import Task, EAS

class EASLazy(EAS):
    def __init__(self, load_gen: LoadGenerator, cpus: list[CPU], em: EnergyModel, driver: Schedutil, sched_tick_period: int = 1) -> None:
        super().__init__(load_gen, cpus, em, driver, sched_tick_period)

    def _find_energy_efficient_cpu(self, by_cpu: CPU, task: Task) -> CPU:
        complexity: int = 0
        
        candidates: list[CPU] = []
        for domain in self._perf_domains_name:
            candidate: CPU = self._cpus_per_domain[domain][0]
            candidate_cap: int = self._run_queues[candidate].cap
            for cpu in self._cpus_per_domain[domain][1:]:
                capacity = self._run_queues[cpu].cap
                if capacity < candidate_cap:
                    candidate = cpu
                    candidate_cap = capacity
            candidates.append(candidate)
            complexity += len(self._cpus_per_domain[domain])

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

        assert(best_cpu is not None)
        return best_cpu