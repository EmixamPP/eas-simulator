from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scheduler import LoadGenerator
    from energy_model import EnergyModel
    from cpu import CPU

from scheduler import EAS

class EASOverutilTwolimitsManycores(EAS):
    def __init__(self, load_gen: LoadGenerator, cpus: list[CPU], em: EnergyModel, sched_tick_period: int = 1, count_limit: int = -1) -> None:
        super().__init__(load_gen, cpus, em, sched_tick_period)
        self._was_over_utilized = False
        
        if count_limit == -1:
            self._count_limit: float = len(self._cpus) / 2
        else: 
            assert(0 <= count_limit <= len(self._cpus))
            self._count_limit = count_limit

    def _is_over_utilized(self) -> bool:
        above_lower_limit = False
        count: int = 0

        for cpu in self._cpus:
            load = self._compute_load(cpu)
            if load >= 80:
                count += 1
                if count >= self._count_limit:
                    self._was_over_utilized = True
                    return True
            elif self._was_over_utilized and load >= 70:
                above_lower_limit = True

        if not above_lower_limit:
            self._was_over_utilized = False

        return above_lower_limit