from scheduler import RunQueue
from cpu import CPU
from profiler import Profiler


class Schedutil:
    def __init__(self, cpus: list[CPU]) -> None:
        self._cpus = cpus

    def update(self, load: dict[CPU, RunQueue], tick: int) -> None:
        total_energy = 0
        for cpu in self._cpus:
            for pstate in cpu.pstates:
                if pstate[0] > load[cpu].cap:
                    cpu.frequency = pstate
                    total_energy += pstate[1]
                    break

        Profiler.update_energy_consumption(total_energy, tick)
