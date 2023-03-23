class Task:
    def __init__(self, nbr_cycles: int, name) -> None:
        self._cycles: int = nbr_cycles
        self._remaining: int = nbr_cycles
        self._terminated: bool = False
        self._name = name
    
    @property
    def name(self) -> str:
        return str(self._name)

    @property
    def remaining_cycles(self) -> int:
        return self._remaining

    @property
    def cycles(self) -> int:
        return self._cycles

    @property
    def executed_cycles(self) -> int:
        return self._cycles - self._remaining

    @property
    def terminated(self) -> bool:
        return self._terminated

    def execute(self, cycles: int) -> None:
        self._remaining -= cycles
        assert(self._remaining >= 0)
        if (self._remaining == 0):
            self._terminated = True
