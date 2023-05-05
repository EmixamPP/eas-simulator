from cpu import CPU
from energy_model import EnergyModel
from scheduler import EAS, LoadGenerator

class EASOverutilManycores(EAS):
    def __init__(self, load_gen: LoadGenerator, cpus: list[CPU], em: EnergyModel, sched_tick_period_ms: int = 1, count_limit: int = -1) -> None:        
        super().__init__(load_gen, cpus, em, sched_tick_period_ms)

        if count_limit == -1:
            self._count_limit: int = int(len(self._cpus) / 2)
        else: 
            assert(0 <= count_limit <= len(self._cpus))
            self._count_limit = count_limit

        

    def _is_over_utilized(self) -> bool:
        count: int = 0
        for cpu in self._cpus:
            if self._compute_load(cpu) > 80:
                count += 1
                if count >= self._count_limit:
                    return True
        return False
