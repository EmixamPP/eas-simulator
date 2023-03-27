from math import inf, log2

from scheduler import LoadGenerator, Task
from energy_model import EM, Schedutil
from cpu import CPU
from profiler import Profiler


class EAS:
    def __init__(self, load_gen: LoadGenerator, cpus: list[CPU], em: EM, govenor: Schedutil, sched_tick_period: int = 1) -> None:
        self._load_gen: LoadGenerator = load_gen
        self._cpus: list[CPU] = cpus
        self._em: EM = em
        self._governor = govenor
        self._sched_tick_period: int = sched_tick_period
        self._run_queues: dict[CPU, RunQueue] = {
            cpu: RunQueue() for cpu in cpus}

    def run(self, sched_ticks: int) -> None:
        for tick in range(sched_ticks):
            # every 0.5 sec rebalance the load if CPU is over utilized (as CFS)
            if tick % 500 == 0 and self._is_over_utilized():
                self._load_balancer()

            # pick the next task to execute on each CPU
            for cpu in self._cpus:
                # new task could be comes at each scheduler tick,
                # and those task are assumed to never sleep or being blocked
                new_task = self._load_gen.gen()
                if new_task is not None:
                    best_cpu = self._wake_up_balancer(cpu, new_task)
                    self._run_queues[best_cpu].insert(new_task)
                    self._governor.update(self._run_queues, tick)
                    Profiler.update_load(self._run_queues, tick)

                queue = self._run_queues[cpu]
                task_node = queue.smallest_vr
                task = task_node.task
                cpu.execute_for(task, self._sched_tick_period)

                if task.name == "idle":
                    pass
                elif not task.terminated:
                    queue.update(task_node)
                else:
                    queue.delete(task_node)

                self._governor.update(self._run_queues, tick)
                Profiler.update_load(self._run_queues, tick)

    # extremely simplefied compared to CFS implementation
    def _load_balancer(self) -> None:
        used_cycles = 0
        idle_cpu = None
        overloaded_cpu = (None, -inf)
        for cpu in self._cpus:
            load = self._compute_load(cpu)
            if load == 0:
                idle_cpu = cpu
            elif overloaded_cpu[1] < load:
                overloaded_cpu = (cpu, load)

        used_cycles += 5 * len(self._cpus)

        if idle_cpu is not None:
            overloaded_runqueue = self._run_queues[overloaded_cpu[0]]
            idle_runqueue = self._run_queues[idle_cpu]
            task_node = overloaded_runqueue.highest_vr
            overloaded_runqueue.delete(task_node)
            idle_runqueue.insert(task_node.task)

            used_cycles += int(log2(overloaded_runqueue.size)
                               * 2 + log2(idle_runqueue.size))

        # responsible of the scheduling group
        self._cpus[0].execute(Task(used_cycles, "balance"))

    def _is_over_utilized(self) -> bool:
        for cpu in self._cpus:
            if self._compute_load(cpu) > 80:  # load in %
                return True
        return False

    def _wake_up_balancer(self, by_cpu: CPU, task: Task) -> CPU:
        if self._is_over_utilized():  # act as CFS
            best_cpu = by_cpu
            for cpu in self._cpus:
                if self._compute_load(cpu) == 0:
                    best_cpu = cpu

            by_cpu.execute(Task(3 * len(self._cpus), "balance"))

        else:
            best_cpu = self._find_energy_efficient_cpu(by_cpu, task)

        return best_cpu

    def _find_energy_efficient_cpu(self, by_cpu: CPU, task: Task) -> CPU:
        used_cycles = 0
        lowest_util = {}
        for cpu in self._cpus:
            domain = cpu.type
            load = self._compute_load(cpu)
            if domain not in lowest_util[domain] or self._compute_load(lowest_util[domain]) > load:
                lowest_util[domain] = cpu

        used_cycles += len(self._cpus) * 4

        lowest_energy = inf
        landscape = {cpu: self._run_queues[cpu].cap for cpu in self._cpus}
        for domain in self._em.perf_domains_name:
            cpu_candidate = lowest_util[domain]
            landscape[cpu_candidate] += task.cycles

            estimation, cycles = self._em.compute_energy(landscape)
            used_cycles += cycles
            if lowest_energy > estimation:
                energy_efficient_cpu = cpu_candidate
                lowest_energy = estimation

            landscape[cpu_candidate] -= task.cycles

        used_cycles += len(self._em.perf_domains_name) * 4

        by_cpu.execute(Task(used_cycles, "energy"))
        return energy_efficient_cpu

    def _compute_load(self, cpu: CPU):
        return self._run_queues[cpu].cap / cpu.max_capacity


"""Initial code comming from https://favtutor.com/blogs/red-black-tree-python
Altough not really a qualitative code, it works and respect the complexity
except on the minimum element access. 
The code has been modified to take into account the fact that this is a run queue."""


class _RunQueueNode():
    def __init__(self, task: Task):
        self._task: Task = task
        self._key: int = task.executed_cycles
        self._cap: int = task.remaining_cycles
        self.parent: _RunQueueNode | None = None
        self.left: _RunQueueNode | None = None
        self.right: _RunQueueNode | None = None
        self.color: int = 1

    @property
    def key(self) -> int:
        return self.task.executed_cycles

    @property
    def cap(self) -> int:
        return self._cap

    @property
    def task(self) -> Task:
        return self._task


class RunQueue():
    def __init__(self):
        self.NULL: _RunQueueNode = _RunQueueNode(Task(-1, "idle"))
        self.NULL.color = 0
        self.root: _RunQueueNode = self.NULL
        self._total_cap: int = 0
        self._size: int = 0

    @property
    def size(self) -> int:
        return self._size

    @property
    def smallest_vr(self) -> _RunQueueNode:  # not in O(1), here
        return self._minimum(self.root)

    @property
    def highest_vr(self) -> _RunQueueNode:  # not in O(1), here
        return self._maximum(self.root)

    @property
    def cap(self) -> int:
        return self._total_cap

    def insert(self, key: Task) -> None:
        self._size += 1
        node = _RunQueueNode(key)
        self._total_cap += node.cap

        y = None
        x = self.root

        while x != self.NULL:
            y = x
            if node.key < x.key:
                x = x.left
            else:
                x = x.right

        node.parent = y
        if y == None:
            self.root = node
        elif node.key < y.key:
            y.left = node
        else:
            y.right = node

        if node.parent == None:
            node.color = 0
            return

        if node.parent.parent == None:
            return

        self._fix_insert(node)

    def _minimum(self, node) -> _RunQueueNode:
        while node.left is not None:
            node = node.left
        return node

    def _maximum(self, node) -> _RunQueueNode:
        while node.right is not None:
            node = node.right
        return node

    def _left_rotation(self, x):
        y = x.right
        x.right = y.left
        if y.left != self.NULL:
            y.left.parent = x

        y.parent = x.parent
        if x.parent == None:
            self.root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y

    def _rotate_right(self, x):
        y = x.left
        x.left = y.right
        if y.right != self.NULL:
            y.right.parent = x

        y.parent = x.parent
        if x.parent == None:
            self.root = y
        elif x == x.parent.right:
            x.parent.right = y
        else:
            x.parent.left = y
        y.right = x
        x.parent = y

    def _fix_insert(self, k):
        while k.parent.color == 1:
            if k.parent == k.parent.parent.right:
                u = k.parent.parent.left
                if u.color == 1:
                    u.color = 0
                    k.parent.color = 0
                    k.parent.parent.color = 1
                    k = k.parent.parent
                else:
                    if k == k.parent.left:
                        k = k.parent
                        self._rotate_right(k)
                    k.parent.color = 0
                    k.parent.parent.color = 1
                    self._left_rotation(k.parent.parent)
            else:
                u = k.parent.parent.right
                if u.color == 1:
                    u.color = 0
                    k.parent.color = 0
                    k.parent.parent.color = 1
                    k = k.parent.parent
                else:
                    if k == k.parent.right:
                        k = k.parent
                        self._left_rotation(k)
                    k.parent.color = 0
                    k.parent.parent.color = 1
                    self._rotate_right(k.parent.parent)
            if k == self.root:
                break
        self.root.color = 0

    def _fix_delete(self, x):
        while x != self.root and x.color == 0:
            if x == x.parent.left:
                s = x.parent.right
                if s.color == 1:
                    s.color = 0
                    x.parent.color = 1
                    self._left_rotation(x.parent)
                    s = x.parent.right
                if s.left.color == 0 and s.right.color == 0:
                    s.color = 1
                    x = x.parent
                else:
                    if s.right.color == 0:
                        s.left.color = 0
                        s.color = 1
                        self._rotate_right(s)
                        s = x.parent.right

                    s.color = x.parent.color
                    x.parent.color = 0
                    s.right.color = 0
                    self._left_rotation(x.parent)
                    x = self.root
            else:
                s = x.parent.left
                if s.color == 1:
                    s.color = 0
                    x.parent.color = 1
                    self._rotate_right(x.parent)
                    s = x.parent.left

                if s.right.color == 0 and s.right.color == 0:
                    s.color = 1
                    x = x.parent
                else:
                    if s.left.color == 0:
                        s.right.color = 0
                        s.color = 1
                        self._left_rotation(s)
                        s = x.parent.left

                    s.color = x.parent.color
                    x.parent.color = 0
                    s.left.color = 0
                    self._rotate_right(x.parent)
                    x = self.root
        x.color = 0

    def _rb_transplant(self, u, v):
        if u.parent == None:
            self.root = v
        elif u == u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        v.parent = u.parent

    def delete(self, node: _RunQueueNode) -> None:
        self._size -= 1
        self._total_cap -= node.cap

        z = node
        y = z
        y_original_color = y.color
        if z.left == self.NULL:
            x = z.right
            self._rb_transplant(z, z.right)
        elif (z.right == self.NULL):
            x = z.left
            self._rb_transplant(z, z.left)
        else:
            y = self._minimum(z.right)
            y_original_color = y.color
            x = y.right
            if y.parent == z:
                x.parent = y
            else:
                self._rb_transplant(y, y.right)
                y.right = z.right
                y.right.parent = y

            self._rb_transplant(z, y)
            y.left = z.left
            y.left.parent = y
            y.color = z.color
        if y_original_color == 0:
            self._fix_delete(x)

    def update(self, node: _RunQueueNode) -> None:
        self.delete(node)
        self.insert(node.task)
