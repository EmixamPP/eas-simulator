from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cpu import CPU, PerfDom
    from scheduler import LoadGenerator
    from energy_model import EnergyModel, Schedutil

import math

from scheduler import Task, EAS
from profiler import Profiler

class EASCorechoiceNextfit(EAS):
    def __init__(self, load_gen: LoadGenerator, cpus: list[CPU], em: EnergyModel, driver: Schedutil, sched_tick_period: int = 1) -> None:
        super().__init__(load_gen, cpus, em, driver, sched_tick_period)
        self._best_cpu_index: dict[PerfDom, int] = {domain: 0 for domain in self._perf_domains_name}

    def _find_energy_efficient_cpu(self, by_cpu: CPU, task: Task) -> CPU:
        used_cycles: int = 0
        candidates: dict[PerfDom, CPU] = {}
        
        for domain in self._perf_domains_name:
            cpus = self._cpus_per_domain[domain]
            i: int = self._best_cpu_index[domain]
            previous_best_cpu_load: float = self._compute_load(cpus[i])
            cpu: CPU = cpus[++i]
            used_cycles += 4

            while self._compute_load(cpu) <= previous_best_cpu_load:
                cpu: CPU = cpus[++i]
                used_cycles += 4

            candidates[domain] = cpu

        lowest_energy: int | float = math.inf
        energy_efficient_cpu: CPU | None = None
        landscape: dict[CPU, int] = {
            cpu: self._run_queues[cpu].cap for cpu in self._cpus}
        
        used_cycles += len(self._run_queues)

        for domain in self._perf_domains_name:
            cpu_candidate: CPU = candidates[domain]
            landscape[cpu_candidate] += task.remaining_cycles

            estimation, cycles = self._em.compute_energy(landscape)
            used_cycles += cycles
            if lowest_energy > estimation:
                energy_efficient_cpu = cpu_candidate
                lowest_energy = estimation

            landscape[cpu_candidate] -= task.remaining_cycles

        used_cycles += len(self._perf_domains_name) * 4

        # simulate the energy efficient wake up balancer
        Profiler.new_task()
        self._run_queues[by_cpu].insert_kernel_task(Task(used_cycles, "energy"))

        assert(energy_efficient_cpu is not None)
        return energy_efficient_cpu