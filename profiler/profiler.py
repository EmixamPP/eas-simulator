import math


class Profiler:
    def __init__(self) -> None:
        self._total_energy: float = 0
        self._cpu_power_timestamp: dict[str, tuple[int, int]] = {}

        # one index for each task type: common, energy, balance, idle
        self._cycles_hist: list[int] = [0, 0, 0, 0]

        self._created_task: int = 0
        self._ended_task: int = 0

    def reset(self):
        self.__init__()

    def executed_for(self, task_name: str, cycles: int) -> None:
        i = 0
        match task_name:
            case "energy":
                i = 1
            case "balance":
                i = 2
            case "idle":
                i = 3
        self._cycles_hist[i] += cycles

    def new_task(self) -> None:
        self._created_task += 1

    def end_task(self) -> None:
        self._ended_task += 1

    def update_power_consumption(self, power: int, timestamp_ms: int, cpu_name: str) -> None:
        if cpu_name in self._cpu_power_timestamp:
            previous_power = self._cpu_power_timestamp[cpu_name][0]
            previous_timestamp = self._cpu_power_timestamp[cpu_name][1]
            self._total_energy += previous_power * \
                (timestamp_ms - previous_timestamp)  # TODO * 10**-3

        self._cpu_power_timestamp[cpu_name] = (power, timestamp_ms)

    @property
    def created_task(self) -> int:
        return self._created_task

    @property
    def ended_task(self) -> int:
        return self._ended_task

    @property
    def cycles_repartition(self) -> tuple[float, float, float, float]:
        total_cycles = sum(self._cycles_hist)
        return tuple([i/total_cycles*100 for i in self._cycles_hist])

    @property
    def cycles_hist(self) -> tuple[int, int, int, int]:
        return tuple(self._cycles_hist)

    @property
    def total_energy(self) -> int:
        return math.ceil(self._total_energy)
