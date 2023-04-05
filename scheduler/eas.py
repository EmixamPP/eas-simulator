from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scheduler import LoadGenerator
    from energy_model import EnergyModel, Schedutil
    from cpu import CPU, PerfDom

from math import inf, log2, ceil
import heapq

from scheduler import Task
from profiler import Profiler


class EAS:
    def __init__(self, load_gen: LoadGenerator, cpus: list[CPU], em: EnergyModel, driver: Schedutil, sched_tick_period: int = 1) -> None:
        self._load_gen: LoadGenerator = load_gen
        self._cpus: list[CPU] = cpus
        self._em: EnergyModel = em
        self._driver = driver
        self._sched_tick_period: int = sched_tick_period  # ms
        self._run_queues: dict[CPU, RunQueue] = {
            cpu: RunQueue() for cpu in cpus}
        self._idle_task = Task(-1, "idle")

    def run(self, time: int) -> None:
        for tick in range(time):
            # every 1000 tick rebalance the load if CPU is over utilized (~ as CFS, which is every 1000ms)
            if tick % 1000 == 0 and self._is_over_utilized():
                self._load_balancer()

            # pick the next task to execute on each CPU
            for cpu in self._cpus:
                # new task could be comes at each scheduler tick,
                # and those task are assumed to never sleep or being blocked
                new_task: Task | None = self._load_gen.gen()
                if new_task is not None:
                    Profiler.new_task()
                    best_cpu: CPU = self._wake_up_balancer(cpu, new_task)
                    self._run_queues[best_cpu].insert(new_task)

                queue: RunQueue = self._run_queues[cpu]
                task: Task | None = queue.pop_smallest_vr()
                if task is None:
                    task = self._idle_task
                
                cpu.execute_for(task, self._sched_tick_period)
                if task.name != "idle":
                    if not task.terminated:
                        queue.insert(task)
                    else:
                        Profiler.end_task()


            self._driver.update(self._run_queues)

    # extremely simplefied compared to CFS implementation
    def _load_balancer(self) -> None:
        used_cycles: int = 0
        idle_cpu: CPU | None = None
        overloaded_cpu: tuple[CPU | None, int | float] = (None, -inf)
        for cpu in self._cpus:
            load: float = self._compute_load(cpu)
            if load == 0.0:
                idle_cpu = cpu
            elif overloaded_cpu[1] < load:
                overloaded_cpu = (cpu, load)

        used_cycles += 5 * len(self._cpus)

        if idle_cpu is not None:
            assert(overloaded_cpu[0] is not None)
            overloaded_runqueue: RunQueue = self._run_queues[overloaded_cpu[0]]
            idle_runqueue: RunQueue = self._run_queues[idle_cpu]
            task: Task | None = overloaded_runqueue.pop_highest_vr()
            if task is not None:
                idle_runqueue.insert(task)

            if overloaded_runqueue.size != 0:
                used_cycles += ceil(log2(overloaded_runqueue.size) * 2)
            if idle_runqueue.size != 0:
                used_cycles += ceil(log2(idle_runqueue.size))

        # responsible of the scheduling group
        self._cpus[0].execute(Task(used_cycles, "balance"))

    def _is_over_utilized(self) -> bool:
        for cpu in self._cpus:
            if self._compute_load(cpu) > 80:
                return True
        return False

    def _wake_up_balancer(self, by_cpu: CPU, task: Task) -> CPU:
        if self._is_over_utilized():  # act as CFS
            best_cpu: CPU = by_cpu
            for cpu in self._cpus:
                if self._run_queues[cpu].cap == 0:
                    best_cpu = cpu
            by_cpu.execute(Task(3 * len(self._cpus), "balance"))
        else:
            best_cpu = self._find_energy_efficient_cpu(by_cpu, task)

        return best_cpu

    def _find_energy_efficient_cpu(self, by_cpu: CPU, task: Task) -> CPU:
        used_cycles: int = 0
        lowest_util: dict[PerfDom, CPU] = {}
        # find in each domain the cpu with the lower util
        for cpu in self._cpus:
            domain: PerfDom = cpu.type
            load: float = self._compute_load(cpu)
            if domain not in lowest_util or self._compute_load(lowest_util[domain]) > load:
                lowest_util[domain] = cpu

        used_cycles += len(self._cpus) * 4

        lowest_energy: int | float = inf
        energy_efficient_cpu: CPU | None = None
        landscape: dict[CPU, int] = {
            cpu: self._run_queues[cpu].cap for cpu in self._cpus}

        used_cycles += len(self._run_queues)

        for domain in self._em.perf_domains_name:
            cpu_candidate: CPU = lowest_util[domain]
            landscape[cpu_candidate] += task.cycles

            estimation, cycles = self._em.compute_energy(landscape)
            used_cycles += cycles
            if lowest_energy > estimation:
                energy_efficient_cpu = cpu_candidate
                lowest_energy = estimation

            landscape[cpu_candidate] -= task.cycles

        used_cycles += len(self._em.perf_domains_name) * 4

        by_cpu.execute(Task(used_cycles, "energy"))

        assert(energy_efficient_cpu is not None)
        return energy_efficient_cpu

    def _compute_load(self, cpu: CPU) -> float:
        return self._run_queues[cpu].cap / cpu.max_capacity * 100


### easier to implement heap queue instead of Red Black tree, but nothing change for our analyses ###
class _RunQueueNode():
    def __init__(self, task: Task):
        self._task: Task = task
        self._key: int = task.executed_cycles
        self._cap: int = task.remaining_cycles

    @property
    def key(self) -> int:
        return self._key

    @property
    def cap(self) -> int:
        return self._cap

    @property
    def task(self) -> Task:
        return self._task

    def __lt__(self, obj):
        return self.key < obj.key

    def __le__(self, obj):
        return self.key <= obj.key

    def __eq__(self, obj):
        return self.key == obj.key

    def __ne__(self, obj):
        return self.key != obj.key

    def __gt__(self, obj):
        return self.key > obj.key

    def __ge__(self, obj):
        return self.key >= obj.key


class RunQueue():
    def __init__(self):
        self._queue: list[_RunQueueNode] = []
        self._total_cap: int = 0

    @property
    def size(self) -> int:
        return len(self._queue)

    def pop_smallest_vr(self) -> None | Task:
        if self.size == 0:
            return None
        task_node: _RunQueueNode = heapq.heappop(self._queue)
        self._total_cap -= task_node.cap
        return task_node.task

    def pop_highest_vr(self) -> None | Task:
        if self.size == 0:
            return None
        index_max: int = max(range(len(self._queue)),
                             key=self._queue.__getitem__)
        task_node: _RunQueueNode = self._queue[index_max]
        self._total_cap -= task_node.cap
        del self._queue[index_max]
        heapq.heapify(self._queue)
        return task_node.task

    @property
    def cap(self) -> int:
        return self._total_cap

    def insert(self, task: Task):
        task_node = _RunQueueNode(task)
        self._total_cap += task_node.cap
        heapq.heappush(self._queue, task_node)
