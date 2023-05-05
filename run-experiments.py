from typing import Any

import math
import numpy as np
import multiprocessing
import time

from scheduler import EAS, LoadGenerator, EASOverutilDisabled, EASOverutilTwolimits, EASOverutilManycores, EASOverutilTwolimitsManycores, EASCorechoiceNextfit, EASCorechoiceNextfitOverutilTwolimits
from energy_model import EnergyModel
from cpu import CPU, CPUGenerator


REPETITION = 100
RANDOM_SEED = 1
PICK_DISTRIB_INTS: int = math.floor(0.1 * 10**9)
MAX_DISTRIB_INSTS: int = math.floor(4 * 10**9)
CREATE_TASK_PROB: float = 0.999


def _write_results(diff_hist: dict[str, tuple[list[float], list[float], list[float], list[float], list[float], list[float]]], file_name: str):
    # compute means and variances of difference history
    diff_mean_var: dict[str, dict[str, tuple[Any, Any]]] = {}

    for version_name in diff_hist.keys():
        diff_mean_var[version_name] = {}
        mean_var = diff_mean_var[version_name]

        hist = diff_hist[version_name]

        mean_var["total_energy"] = (np.mean(hist[0]), np.var(hist[0]))
        mean_var["task"] = (np.mean(hist[1]), np.var(hist[1]))
        mean_var["energy"] = (np.mean(hist[2]), np.var(hist[2]))
        mean_var["balance"] = (np.mean(hist[3]), np.var(hist[3]))
        mean_var["idle"] = (np.mean(hist[4]), np.var(hist[4]))

    # output results
    with open(file_name, "w") as f:
        f.write("Version,Energy mean,Energy var,Task cycles mean,Task cycles var,Energy cycles mean,Energy cycles var,Balance cycles mean,Balance cycles var,Idle cycles mean,Idle cycles var\n")
        for version_name in diff_hist.keys():
            mean_var = diff_mean_var[version_name]
            f.write(f"{version_name},")
            f.write("{},{},".format(
                np.round(mean_var["total_energy"][0], 1), np.round(mean_var["total_energy"][1], 1)))
            f.write("{},{},".format(
                np.round(mean_var["task"][0], 1), np.round(mean_var["task"][1], 1)))
            f.write("{},{},".format(
                np.round(mean_var["energy"][0], 1), np.round(mean_var["energy"][1], 1)))
            f.write("{},{},".format(
                np.round(mean_var["balance"][0], 1), np.round(mean_var["balance"][1], 1)))
            f.write("{},{}\n".format(
                np.round(mean_var["idle"][0], 1), np.round(mean_var["idle"][1], 1)))


def run_experiment_on(cpus: list[CPU], cpus_description: str):
    print(f"Stating experiment on: {cpus_description}")

    versions: list[type] = [
        EAS,
        EASOverutilDisabled,
        EASOverutilTwolimits,
        EASOverutilManycores,
        EASOverutilTwolimitsManycores,
        EASCorechoiceNextfit,
        EASCorechoiceNextfitOverutilTwolimits
    ]

    em: EnergyModel = EnergyModel(cpus)
    load_generators: dict[type, LoadGenerator] = {version: LoadGenerator(
        PICK_DISTRIB_INTS, MAX_DISTRIB_INSTS, CREATE_TASK_PROB, RANDOM_SEED) for version in versions}

    diff_hist: dict[str, tuple[list[float], list[float], list[float], list[float], list[float], list[float]]] = {
        version.__name__: ([], [], [], [], [], []) for version in versions[1:]}

    for _ in range(REPETITION):
        eas_hist = (0, 0, 0, 0, 0, 0)
        for version in versions:
            scheduler = version(load_generators[version], cpus, em)
            scheduler.run(60000)
            profiler = scheduler.profiler

            power = profiler.total_energy
            task_cycles = profiler.cycles_hist[0]
            energy_cycles = profiler.cycles_hist[1]
            balance_cycles = profiler.cycles_hist[2]
            idle_cycles = profiler.cycles_hist[3]

            if version == EAS:
                eas_hist = (power, task_cycles, energy_cycles,
                            balance_cycles, idle_cycles)
            else:
                hist = diff_hist[version.__name__]
                hist[0].append((power / eas_hist[0] - 1) * 100)
                hist[1].append((task_cycles / eas_hist[1] - 1) * 100)
                hist[2].append((energy_cycles / eas_hist[2] - 1) * 100)
                hist[3].append((balance_cycles / eas_hist[3] - 1) * 100)
                hist[4].append((idle_cycles / eas_hist[4] - 1) * 100)

    _write_results(
        diff_hist, f"results_{cpus_description}.csv".replace(" ", "_"))

    print(f"Ending experiment on: {cpus_description}")


def run_extra_experiment_calibration_on(cpus: list[CPU], cpus_description: str):
    print(f"Stating extra experiment for calibration on: {cpus_description}")

    em: EnergyModel = EnergyModel(cpus)
    load_generators: dict[str, LoadGenerator] = {"EAS": LoadGenerator(
        PICK_DISTRIB_INTS, MAX_DISTRIB_INSTS, CREATE_TASK_PROB, RANDOM_SEED)}

    diff_hist: dict[str, tuple[list[float], list[float],
                               list[float], list[float], list[float], list[float]]] = {}

    for count_limit in range(1, int(len(cpus) / 2) + 1):
        load_generators[f"EASOverutil{count_limit}cores"] = LoadGenerator(
            PICK_DISTRIB_INTS, MAX_DISTRIB_INSTS, CREATE_TASK_PROB, RANDOM_SEED)
        diff_hist[f"EASOverutil{count_limit}cores"] = ([], [], [], [], [], [])

    for _ in range(REPETITION):
        scheduler = EAS(load_generators["EAS"], cpus, em)
        scheduler.run(60000)
        profiler = scheduler.profiler

        power = profiler.total_energy
        task_cycles = profiler.cycles_hist[0]
        energy_cycles = profiler.cycles_hist[1]
        balance_cycles = profiler.cycles_hist[2]
        idle_cycles = profiler.cycles_hist[3]

        eas_hist = (power, task_cycles, energy_cycles,
                    balance_cycles, idle_cycles)

        for count_limit in range(1, int(len(cpus) / 2) + 1):
            scheduler = EASOverutilManycores(
                load_generators[f"EASOverutil{count_limit}cores"], cpus, em, count_limit=count_limit)
            scheduler.run(60000)
            profiler = scheduler.profiler

            power = profiler.total_energy
            task_cycles = profiler.cycles_hist[0]
            energy_cycles = profiler.cycles_hist[1]
            balance_cycles = profiler.cycles_hist[2]
            idle_cycles = profiler.cycles_hist[3]

            hist = diff_hist[f"EASOverutil{count_limit}cores"]
            hist[0].append((power / eas_hist[0] - 1) * 100)
            hist[1].append((task_cycles / eas_hist[1] - 1) * 100)
            hist[2].append((energy_cycles / eas_hist[2] - 1) * 100)
            hist[3].append((balance_cycles / eas_hist[3] - 1) * 100)
            hist[4].append((idle_cycles / eas_hist[4] - 1) * 100)

    _write_results(
        diff_hist, f"calibration_results_{cpus_description}.csv".replace(" ", "_"))

    print(f"Ending extra experiment for calibration on: {cpus_description}")


if __name__ == "__main__":
    start_time = time.time()

    experiment_args: list[tuple[list[CPU], str]] = [
        (CPUGenerator.gen(little=2, middle=2), "2 little 2 middle"),
        (CPUGenerator.gen(little=4, middle=4), "4 little 4 middle"),
        (CPUGenerator.gen(little=8, middle=8), "8 little 8 middle"),
        (CPUGenerator.gen(little=16, middle=16), "16 little 16 middle"),
        (CPUGenerator.gen(little=32, middle=32), "32 little 32 middle"),
        (CPUGenerator.gen(little=16, middle=16, big=16), "16 little 16 middle 16 big"),
        (CPUGenerator.gen(little=32, middle=32, big=32), "32 little 32 middle 32 big")
    ]

    processes = []
    for cpus, cpus_description in experiment_args:
        proc = multiprocessing.Process(
            target=run_experiment_on, args=(cpus, cpus_description))
        proc.start()
        processes.append(proc)

    proc = multiprocessing.Process(
        target=run_extra_experiment_calibration_on, args=(CPUGenerator.gen(little=8, middle=8), "8 little 8 middle"))
    proc.start()
    processes.append(proc)

    for proc in processes:
        proc.join()

    end_time = time.time()
    print("Min. elasped:", (end_time - start_time) / 60)
