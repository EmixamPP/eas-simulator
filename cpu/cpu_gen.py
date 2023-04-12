import copy
import math

from cpu import CPU, PerfDom, PState


class CPUGenerator:
    def __init__(self) -> None:
        def FREQ(fGHZ) -> int: return int(fGHZ * 10**9)
        def ENERGY(fGHZ) -> int: return math.ceil(fGHZ**1.5 * 10)

        self.little_cpu_template = CPU(PerfDom("little"), [
            PState((FREQ(0.5), ENERGY(0.5))),
            PState((FREQ(0.75), ENERGY(0.75))),
            PState((FREQ(1), ENERGY(1))),
            PState((FREQ(1.25), ENERGY(1.25))),
            PState((FREQ(1.5), ENERGY(1.5))),
            PState((FREQ(1.75), ENERGY(1.75))),
            PState((FREQ(2), ENERGY(2)))
        ], "little")

        self.middle_cpu_template = CPU(PerfDom("middle"), [
            PState((FREQ(1.5), ENERGY(1.5))),
            PState((FREQ(1.75), ENERGY(1.75))),
            PState((FREQ(2), ENERGY(2))),
            PState((FREQ(2.25), ENERGY(2.25))),
            PState((FREQ(2.5), ENERGY(2.5))),
            PState((FREQ(2.75), ENERGY(2.75))),
            PState((FREQ(3), ENERGY(3)))
        ], "middle")

        self.big_cpu_template = CPU(PerfDom("big"), [
            PState((FREQ(2.5), ENERGY(2.5))),
            PState((FREQ(2.75), ENERGY(2.75))),
            PState((FREQ(3), ENERGY(3))),
            PState((FREQ(3.25), ENERGY(3.25))),
            PState((FREQ(3.5), ENERGY(3.5))),
            PState((FREQ(3.75), ENERGY(3.75))),
            PState((FREQ(4), ENERGY(4)))
        ], "big")

    def gen(self, little: int = 0, middle: int = 0, big: int = 0) -> list[CPU]:
        cpus: list[CPU] = []
        i: int = -1
        for _ in range(little):
            cpus.append(copy.deepcopy(self.little_cpu_template))
            cpus[-1].name = f"cpu{++i}"
        for _ in range(middle):
            cpus.append(copy.deepcopy(self.middle_cpu_template))
            cpus[-1].name = f"cpu{++i}"
        for _ in range(big):
            cpus.append(copy.deepcopy(self.big_cpu_template))
            cpus[-1].name = f"cpu{++i}"
        return cpus
