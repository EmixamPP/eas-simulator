from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scheduler import Clock

import math


class Profiler:
    def __init__(self, clock: Clock) -> None:
        self._clock = clock

        self._total_energy: int = 0
        self._cpu_power_timestamp: dict[str, tuple[int, int]] = {}

        # one index for each task type: common, energy, balance, idle, slack
        self._cycles_hist: list[int] = [0, 0, 0, 0, 0]

        self._created_task: int = 0
        self._ended_task: int = 0
        self._task_placed_energy_aware: int = 0
        self._task_placed_load_balancing: int = 0

    def executed_for(self, task_name: str, cycles: int) -> None:
        i = 0
        match task_name:
            case "energy":
                i = 1
            case "balance":
                i = 2
            case "idle":
                i = 3
            case "slack":
                i = 4
        self._cycles_hist[i] += cycles

    def new_task(self) -> None:
        self._created_task += 1

    def end_task(self) -> None:
        self._ended_task += 1

    def update_power_consumption(self, power: int, cpu_name: str) -> None:
        if cpu_name in self._cpu_power_timestamp:
            previous_power = self._cpu_power_timestamp[cpu_name][0]
            previous_timestamp = self._cpu_power_timestamp[cpu_name][1]
            self._total_energy += previous_power * \
                (self._clock.time - previous_timestamp)

        self._cpu_power_timestamp[cpu_name] = (power, self._clock.time)

    @property
    def created_task(self) -> int:
        return self._created_task

    @property
    def ended_task(self) -> int:
        return self._ended_task

    @property
    def cycles_hist(self) -> tuple[int, int, int, int, int]:
        return tuple(self._cycles_hist)

    @property
    def total_energy(self) -> int:
        return math.ceil(self._total_energy)
    
    def task_placed_by(self, wakeup_algo: str) -> None:
        if wakeup_algo == "energy":
            self._task_placed_energy_aware += 1
        elif wakeup_algo == "balance":
            self._task_placed_load_balancing += 1

    @property
    def task_placed_energy_aware(self) -> int:
        return self._task_placed_energy_aware

    @property
    def task_placed_by_load_balancing(self) -> int:
        return self._task_placed_load_balancing
    
    @property
    def cycles_repartition(self) -> tuple[float, float, float, float, float]:
        total_cycles = sum(self._cycles_hist)
        print(self._cycles_hist[1]/total_cycles*100)
        return tuple([i/total_cycles*100 for i in self._cycles_hist])
