from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cpu import CPU
    from scheduler import LoadGenerator
    from energy_model import EnergyModel

from scheduler import EASCorechoiceNextfit, EASOverutilTwolimits

class EASCorechoiceNextfitOverutilTwolimits(EASCorechoiceNextfit, EASOverutilTwolimits):
    def __init__(self, load_gen: LoadGenerator, cpus: list[CPU], em: EnergyModel, sched_tick_period: int = 1) -> None:
        super().__init__(load_gen, cpus, em, sched_tick_period)