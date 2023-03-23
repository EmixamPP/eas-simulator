from numpy import random

from scheduler import Task


class LoadGenerator:
    def __init__(self, instructions_peak_distrib: int, max_instructions: int) -> None:
        self._insts_peak_distrib: int = instructions_peak_distrib
        self._max_instructions: int = max_instructions
        self._uuid = -1
    
    def _generate_random_task(self) -> Task:
        insts = int(random.triangular(0, self._insts_peak_distrib, self._max_instructions))
        self._uuid += 1
        return Task(insts, self._uuid)

    def __next__(self) -> None | Task:
        return self.gen()

    def __iter__(self):
        return self

    def gen(self) -> None | Task:
        if random.random() >= 0.5:
            return self._generate_random_task()
