from energy_model import EM
from cpu import CPU

class EMenhanced(EM):
    def __init__(self, cpus: list[CPU]) -> None:
        super().__init__(cpus)
    
    def compute_energy(self, landscape: dict[CPU, int]) -> int:
        return 0 # TODO