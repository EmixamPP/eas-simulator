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


class Nextfit(Placer):
    def __init__(self, nbr_bin: int) -> None:
        super().__init__(nbr_bin)
        self.prev_bin_i: int = 0

    def place(self, item: float) -> None:
        bin_i: int = (self.prev_bin_i + 1) % len(self.bins)
        bin = self.bins[bin_i]
        self.total_step += 1

        self.prev_bin_i = bin_i
        bin.place(item)


def compute_boxplot(data: np.ndarray):
    median = np.percentile(data, 50)
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    whisker_min = data[data >=
                       q1 - 1.5 * iqr].min()
    whisker_max = data[data <=
                       q3 + 1.5 * iqr].max()
    outers = data[(data < whisker_min) | (
        data > whisker_max)]
    return (median.round(2), q1.round(2), q3.round(2), whisker_min.round(2), whisker_max.round(2), outers.round(2))


def run_experiment_with(nbr_bin: int):
    with open(f"diff_std_binpacking_{nbr_bin}bins.csv", "w") as file:
        file.write("items, median, q1, q3, whisker_min, whisker_max, outers\n")

        for nbr_item in [nbr_bin * 2, nbr_bin * 4, nbr_bin * 8]:

            nextfitcond_std_diff_hist = []
            nextfit_std_diff_hist = []
            nextfitcond_step_hist = []
            for repetition in range(10000):

                worstfit: Placer = Worstfit(nbr_bin)
                nextfitcond: Placer = NextfitCond(nbr_bin)
                nextfit: Placer = Nextfit(nbr_bin)

                gen: npr.Generator = npr.Generator(npr.PCG64(repetition))
                items = gen.random(nbr_item)
                for item in items:
                    worstfit.place(item)
                    nextfitcond.place(item)
                    nextfit.place(item)

                worstfit_std = np.array(
                    [worstfit.bins[i].cap for i in range(nbr_bin)]).std()
                nextfitcond_std = np.array(
                    [nextfitcond.bins[i].cap for i in range(nbr_bin)]).std()
                nextfit_std = np.array(
                    [nextfit.bins[i].cap for i in range(nbr_bin)]).std()

                nextfitcond_std_diff_hist.append(worstfit_std - nextfitcond_std)
                nextfit_std_diff_hist.append(worstfit_std - nextfit_std)
                nextfitcond_step_hist.append(nextfitcond.total_step)

            median, q1, q3, whisker_min, whisker_max, outers = compute_boxplot(
                np.array(nextfitcond_std_diff_hist))
            file.write(
                f"nextfitcond_std_items{nbr_item}, {median}, {q1}, {q3}, {whisker_min}, {whisker_max}, {tuple(outers)}\n")

            median, q1, q3, whisker_min, whisker_max, outers = compute_boxplot(
                np.array(nextfitcond_step_hist))
            file.write(
                f"nextfitcond_step_items{nbr_item}, {median}, {q1}, {q3}, {whisker_min}, {whisker_max}, {tuple(outers)}\n")

            median, q1, q3, whisker_min, whisker_max, outers = compute_boxplot(
                np.array(nextfit_std_diff_hist))
            file.write(
                f"nextfit_std_items{nbr_item}, {median}, {q1}, {q3}, {whisker_min}, {whisker_max}, {tuple(outers)}\n")


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
