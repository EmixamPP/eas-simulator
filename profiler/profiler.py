from scheduler import Task, RunQueue
from cpu import CPU


# TODO:
#   - plot load per cpu over time (2D)
#   - plot task with their cycles per CPU with color accent on Task with name "idle" and "energy" (1D)
#   - plot total energy over time (2D)
class Profiler:
    def __init__(self) -> None:
        pass

    def update_load(self, load: dict[CPU, RunQueue], timestamp_ns: int):
        pass

    def executed_for_on(self, task: Task, cycles: int, cpu: CPU):
        pass
    
    def update_energy_consumption(self, energy: int, timestamp_ns: int):
        pass

    def reset(self):
        pass

    def stash(self):
        pass

    def unstash(self):
        pass

    def generate_plots(self):
        pass
