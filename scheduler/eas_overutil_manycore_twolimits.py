from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scheduler import LoadGenerator
    from energy_model import EnergyModel
    from cpu import CPU
    from profiler import Profiler

from scheduler import EAS

class EASOverutilTwolimitsManycores(EAS):
    def __init__(self, load_gen: LoadGenerator, cpus: list[CPU], em: EnergyModel, profiler: Profiler, sched_tick_period: int = 1) -> None:
        self._was_over_utilized = False
        super().__init__(load_gen, cpus, em, profiler, sched_tick_period)

    def _is_over_utilized(self) -> bool:
        above_lower_limit = False
        count: int = 0
        count_limit: float = len(self._cpus) / 2

        for cpu in self._cpus:
            load = self._compute_load(cpu)
            if load >= 80:
                count += 1
                if count >= count_limit:
                    self._was_over_utilized = True
                    return True
            elif self._was_over_utilized and load >= 70:
                above_lower_limit = True

        if not above_lower_limit:
            self._was_over_utilized = False

        return above_lower_limit