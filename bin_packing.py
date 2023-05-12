import multiprocessing
import time
import numpy as np
npr = np.random


class Bin:
    def __init__(self) -> None:
        self.cap: float = 0

    def place(self, item: float) -> None:
        self.cap += item


class Placer:
    def __init__(self, nbr_bin: int) -> None:
        self.bins: list[Bin] = [Bin() for _ in range(nbr_bin)]
        self.total_step = 0

    def place(self, item: float) -> None:
        raise NotImplementedError()


class Worstfit(Placer):
    def place(self, item: float) -> None:
        bin = min(self.bins, key=lambda bin: bin.cap)
        self.total_step += len(self.bins)
        bin.place(item)


class NextfitCond(Placer):
    def __init__(self, nbr_bin: int) -> None:
        super().__init__(nbr_bin)
        self.prev_bin_i: int = 0

    def place(self, item: float) -> None:
        bin_i: int = (self.prev_bin_i + 1) % len(self.bins)
        bin = self.bins[bin_i]
        self.total_step += 1

        while (self.bins[self.prev_bin_i].cap < bin.cap):
            bin_i = (bin_i + 1) % len(self.bins)
            bin = self.bins[bin_i]
            self.total_step += 1

        self.prev_bin_i = bin_i
        bin.place(item)


def run_experiment_with(nbr_bin: int):
    with open(f"diff_nextfitcond_worstfit_{nbr_bin}bins.csv", "w") as file_diff,\
            open(f"steps_nextfitcond_worstfit_{nbr_bin}bins.csv", "w") as file_steps:
        for total_val in [20, 60, 100]:
            for nbr_item in [nbr_bin*2, nbr_bin*4]:

                std_diff_hist = []
                step_hist = []
                for repetition in range(10000):

                    gen: npr.Generator = npr.Generator(npr.PCG64(repetition))
                    worstfit: Placer = Worstfit(nbr_bin)
                    nextfit: Placer = NextfitCond(nbr_bin)

                    items = gen.random(nbr_item)
                    items *= (nbr_bin * total_val) / np.sum(items)

                    for item in items:
                        worstfit.place(item)
                        nextfit.place(item)

                    nextfit_loads = np.array(
                        [nextfit.bins[i].cap for i in range(nbr_bin)])
                    nextfit_std = nextfit_loads.std()
                    worstfit_loads = np.array(
                        [worstfit.bins[i].cap  for i in range(nbr_bin)])
                    worstfit_std = worstfit_loads.std()
                    std_diff = worstfit_std / nextfit_std * 100

                    std_diff_hist.append(std_diff)
                    step_hist.append(nextfit.total_step)

                file_diff.write("{}, {}\n".format(
                    f"load{total_val}_items{nbr_item}",
                    str(std_diff_hist)[1:-1]))
                file_steps.write("{}, {}\n".format(
                    f"load{total_val}_items{nbr_item}",
                    str(step_hist)[1:-1]))


if __name__ == "__main__":
    start_time = time.time()

    processes = []
    for nbr_bin in [4, 8, 16, 32]:
        proc = multiprocessing.Process(
            target=run_experiment_with, args=[nbr_bin])
        proc.start()
        processes.append(proc)

    for proc in processes:
        proc.join()

    end_time = time.time()
    print("Sec. elasped:", end_time - start_time)
