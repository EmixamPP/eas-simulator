import numpy.random as npr

from scheduler import Task


class LoadGenerator:
    def __init__(self, instructions_peak_distrib: int, max_instructions: int, gen_prob: float, seed: int | None = None) -> None:
        self._insts_generator = npr.Generator(npr.PCG64(seed))
        self._task_generator = npr.Generator(npr.PCG64(seed))
        self._insts_peak_distrib: int = instructions_peak_distrib
        self._max_instructions: int = max_instructions
        self._uuid: int = -1
        self._gen_prob: float = gen_prob

    def _generate_random_task(self) -> Task:
        insts: int = int(self._insts_generator.triangular(
            10, self._insts_peak_distrib, self._max_instructions))
        self._uuid += 1
        return Task(insts, self._uuid)

    def __next__(self) -> None | Task:
        return self.gen()

    def __iter__(self) -> 'LoadGenerator':
        return self

    def gen(self) -> None | Task:
        if self._task_generator.random() >= self._gen_prob:
            return self._generate_random_task()
