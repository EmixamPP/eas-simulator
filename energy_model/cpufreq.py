from scheduler import RunQueue
from cpu import CPU


class Schedutil:
    @staticmethod
    def update(load: dict[CPU, RunQueue]) -> None:
        for cpu in load.keys():
            for pstate in cpu.pstates:
                if pstate[0] > load[cpu].cap:
                    cpu.frequency = pstate
                    break
