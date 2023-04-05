from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cpu import CPU

from energy_model import EnergyModel

class EMenhanced(EnergyModel):
    def __init__(self, cpus: list[CPU]) -> None:
        super().__init__(cpus)
    
    def compute_energy(self, landscape: dict[CPU, int]) -> int:
        return 0 # TODO