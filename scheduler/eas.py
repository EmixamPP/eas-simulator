from math import inf

from scheduler import LoadGenerator, Task
from energy_model import EM, Schedutil
from cpu import CPU


class EAS:
    def __init__(self, load_gen: LoadGenerator, cpus: list[CPU], em: EM, govenor: Schedutil, sched_tick_period: int = 1) -> None:
        self._load_gen: LoadGenerator = load_gen
        self._cpus: list[CPU] = cpus
        self._em: EM = em
        self._governor = govenor
        self._sched_tick_period: int = sched_tick_period
        self._run_queues: dict[CPU, RunQueue] = {
            cpu: RunQueue() for cpu in cpus}
        self._idle_task = Task(0, "idle")

    def run(self, sched_ticks: int) -> None:
        for tick in range(sched_ticks):
            # every 1 sec rebalance the load if CPU is over utilized (as CFS)
            if tick % 1000 == 0 and self._is_over_utilized():
                self._load_balancer()

            # pick the next task to execute on each CPU
            for cpu in self._cpus:
                # new task could be comes at each scheduler tick,
                # and those task are assumed to never sleep or being blocked
                new_task = self._load_gen.gen()
                if new_task is not None:
                    best_cpu = self._wake_up_balancer(cpu, new_task)
                    self._run_queues[best_cpu].insert(new_task)
                    self._governor.update(self._run_queues)

                queue = self._run_queues[cpu]
                task_node = queue.smallest_vr
                if task_node is not None:
                    task = task_node.task
                    cpu.execute_for(task, self._sched_tick_period)
                    # TODO éviter de devoir del + insert
                    queue.delete(task_node)
                    if not task.terminated:
                        queue.insert(task)
                    self._governor.update(self._run_queues)
                else:
                    cpu.execute_for(self._idle_task,
                                    self._sched_tick_period)  # idle period

    def _load_balancer(self) -> None:
        pass  # TODO

    def _is_over_utilized(self) -> bool:
        for cpu in self._cpus:
            if self._run_queues[cpu].cap / cpu.max_capacity > 80:  # load in %
                return True
        return False

    def _wake_up_balancer(self, curr_cpu: CPU, task: Task) -> CPU:
        if self._is_over_utilized():  # act as CFS
            pass  # TODO
        else:
            return self._find_energy_efficient_cpu(curr_cpu, task)

    def _find_energy_efficient_cpu(self, curr_cpu: CPU, task: Task) -> CPU:
        # TODO simuler ça par une tache
        # TODO consider curr_cpu comme ayant déjà la tâche ?
        lowest_util = {}
        for cpu in self._cpus:
            domain = cpu.type
            load = self._run_queues[cpu].cap / cpu.max_capacity
            if domain not in lowest_util[domain] or self._run_queues[lowest_util[domain]].cap / cpu.max_capacity > load:
                lowest_util[domain] = cpu

        energy_efficient_cpu = None
        lowest_energy = inf
        landscape = {cpu: self._run_queues[cpu].cap for cpu in self._cpus}
        for domain in self._em.perf_domains_name:
            cpu_candidate = lowest_util[domain]
            landscape[cpu_candidate] += task.cycles

            estimation = self._em.compute_energy(landscape)
            if lowest_energy > estimation:
                energy_efficient_cpu = cpu_candidate
                lowest_energy = estimation

            landscape[cpu_candidate] -= task.cycles

        return energy_efficient_cpu


class _RunQueueNode:
    def __init__(self, task: Task) -> None:
        self.task = task
        self.left = None
        self.right = None
        self.parent = None
        self.color = "RED"
        # save to avoid modification TODO faire sans ?
        self._remaining_cycles = task.remaining_cycles
        self._executed_cycles = task.executed_cycles

    @property
    def key(self) -> int:
        # should be the time instead number of cycles,
        # but here we represent task here using an amount of cycles
        return self.executde_cycles

    @property
    def executde_cycles(self) -> int:
        return self._executed_cycles

    @property
    def remaining_cycles(self) -> int:
        return self._remaining_cycles


class RunQueue:
    def __init__(self) -> None:
        self._root = None
        self._leftmost = None
        self._capacity = 0

    @property
    def smallest_vr(self) -> None | _RunQueueNode:
        return None if self._leftmost is None else self._leftmost

    @property
    def cap(self) -> int:
        return self._capacity

    def insert(self, task: Task) -> None:
        node = _RunQueueNode(task)
        self._capacity += node.remaining_cycles

        if self._root is None:
            self._root = node
            self._root.color = "BLACK"
            self._leftmost = self._root
            return

        current = self._root
        parent = None
        while current is not None:
            parent = current
            if node.key < current.key:
                current = current.left
            else:
                current = current.right

        node.parent = parent

        if node.key < parent.key:
            parent.left = node
        else:
            parent.right = node

        if self._leftmost is None or node.key < self._leftmost.key:
            self._leftmost = node

        self._fix_insert(node)

    def delete(self, node: _RunQueueNode) -> None:
        self._capacity -= node.remaining_cycles

        if node.left is None or node.right is None:
            y = node
        else:
            y = self.successor(node)

        if y.left is not None:
            x = y.left
        else:
            x = y.right

        if x is not None:
            x.parent = y.parent

        if y.parent is None:
            self.root = x
        elif y == y.parent.left:
            y.parent.left = x
        else:
            y.parent.right = x

        if y != node:
            node.key = y.key
            node.value = y.value

        if self.leftmost == y:
            if y.right is not None:
                self.leftmost = self.minimum(y.right)
            else:
                self.leftmost = y.parent

        if y.color == "BLACK":
            self._fix_delete(x, y.parent)

    def _fix_insert(self, node) -> None:
        while node.parent is not None and node.parent.color == "RED":
            if node.parent == node.parent.parent.left:
                uncle = node.parent.parent.right

                if uncle is not None and uncle.color == "RED":
                    node.parent.color = "BLACK"
                    uncle.color = "BLACK"
                    node.parent.parent.color = "RED"
                    node = node.parent.parent
                else:
                    if node == node.parent.right:
                        node = node.parent
                        self._left_rotate(node)

                    node.parent.color = "BLACK"
                    node.parent.parent.color = "RED"
                    self._right_rotate(node.parent.parent)
            else:
                uncle = node.parent.parent.left

                if uncle is not None and uncle.color == "RED":
                    node.parent.color = "BLACK"
                    uncle.color = "BLACK"
                    node.parent.parent.color = "RED"
                    node = node.parent.parent
                else:
                    if node == node.parent.left:
                        node = node.parent
                        self._right_rotate(node)

                    node.parent.color = "BLACK"
                    node.parent.parent.color = "RED"
                    self._left_rotate(node.parent.parent)

        self._root.color = "BLACK"

    def _fix_delete(self, x, parent) -> None:
        while x != self.root and (x is None or x.color == "BLACK"):
            if x == parent.left:
                sibling = parent.right

                if sibling.color == "RED":
                    sibling.color = "BLACK"
                    parent.color = "RED"
                    self._left_rotate(parent)
                    sibling = parent.right

                if (sibling.left is None or sibling.left.color == "BLACK") and (sibling.right is None or sibling.right.color == "BLACK"):
                    sibling.color = "RED"
                    x = parent
                    parent = x.parent
                else:
                    if sibling.right is None or sibling.right.color == "BLACK":
                        sibling.left.color = "BLACK"
                        sibling.color = "RED"
                        self._right_rotate(sibling)
                        sibling = parent.right

                    sibling.color = parent.color
                    parent.color = "BLACK"
                    sibling.right.color = "BLACK"
                    self._left_rotate(parent)
                    x = self.root
            else:
                sibling = parent.left

                if sibling.color == "RED":
                    sibling.color = "BLACK"
                    parent.color = "RED"
                    self._right_rotate(parent)
                    sibling = parent.left

                if (sibling.left is None or sibling.left.color == "BLACK") and (sibling.right is None or sibling.right.color == "BLACK"):
                    sibling.color

    def _left_rotate(self, node) -> None:
        right = node.right
        node.right = right.left

        if right.left is not None:
            right.left.parent = node

        right.parent = node.parent

        if node.parent is None:
            self._root = right
        elif node == node.parent.left:
            node.parent.left = right
        else:
            node.parent.right = right

        right.left = node
        node.parent = right

        if node == self._leftmost:
            self._leftmost = right

    def _right_rotate(self, node) -> None:
        left = node.left
        node.left = left.right

        if left.right is not None:
            left.right.parent = node

        left.parent = node.parent

        if node.parent is None:
            self._root = left
        elif node == node.parent.left:
            node.parent.left = left
        else:
            node.parent.right = left

        left.right = node
        node.parent = left

        if left.left is None:
            self._leftmost = left
