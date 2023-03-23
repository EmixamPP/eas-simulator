from scheduler import RunQueue
from cpu import CPU


class Schedutil:
    def __init__(self, cpus: list[CPU]) -> None:
        self._cpus = cpus

    def update(self, load: dict[CPU, RunQueue]) -> None:
        for cpu in self._cpus:
            for pstate in cpu.pstates:
                if pstate[0] > load[cpu].cap:
                    cpu.frequency = pstate
                    break
