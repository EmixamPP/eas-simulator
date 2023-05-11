import math
import numpy as np
import multiprocessing
import time

from scheduler import EAS, LoadGenerator, EASOverutilDisabled, EASOverutilTwolimits, EASOverutilManycores, EASCorechoiceNextfit, EASCorechoiceNextfitOverutilDisabled
from energy_model import EnergyModel
from cpu import CPU, CPUGenerator


REPETITION = 100
RANDOM_SEED = 1
PICK_DISTRIB_INTS: int = math.floor(0.1 * 10**9)
MAX_DISTRIB_INSTS: int = math.floor(4 * 10**9)
CREATE_TASK_PROB: float = 0.999


def _write_differences(diff_hist: dict[str, tuple[list[float], list[float], list[float], list[float], list[float]]], file_name: str):
    # output means of the difference history
    with open(file_name, "w") as f:
        f.write("Version,Energy diff % mean,Task cycles diff % mean,Energy cycles diff % mean,Balance cycles diff % mean,Idle cycles diff % mean\n")
        for version_name in diff_hist.keys():
            hist = diff_hist[version_name]
            f.write("{},{},{},{},{},{}\n".format(
                version_name,
                np.round(np.mean(hist[0]), 1),
                np.round(np.mean(hist[1]), 1),
                np.round(np.mean(hist[2]), 1),
                np.round(np.mean(hist[3]), 1),
                np.round(np.mean(hist[4]), 1),
            ))


def _write_placement(placement_hist: dict[str, tuple[list[int], list[int]]], file_name: str):
    # output means of the task placement history
    with open(file_name, "w") as f:
        f.write("Version,Proportion % of task placed by energy aware mean\n")
        for version_name in placement_hist.keys():
            hist = placement_hist[version_name]
            energy_hist = np.array(hist[0])
            balance_hist = np.array(hist[1])
            total = energy_hist + balance_hist
            energy_propotion = energy_hist / total * 100
            f.write("{},{}\n".format(
                version_name,
                np.round(energy_propotion.mean(), 1),
            ))


def run_experiment_on(cpus: list[CPU], cpus_description: str):
    print(f"Stating experiment on: {cpus_description}")

    versions: list[type] = [
        EAS,
        EASOverutilDisabled,
        EASOverutilTwolimits,
        EASOverutilManycores,
        EASCorechoiceNextfit,
        EASCorechoiceNextfitOverutilDisabled
    ]

    em: EnergyModel = EnergyModel(cpus)
    load_generators: dict[type, LoadGenerator] = {version: LoadGenerator(
        PICK_DISTRIB_INTS, MAX_DISTRIB_INSTS, CREATE_TASK_PROB, RANDOM_SEED) for version in versions}

    diff_hist: dict[str, tuple[list[float], list[float], list[float], list[float], list[float]]] = \
        {version.__name__: ([], [], [], [], []) for version in versions[1:]}

    placement_hist: dict[str, tuple[list[int], list[int]]] = \
        {version.__name__: ([], []) for version in versions}

    # simulate EAS and the variants,
    # and save the differences w.r.t. to EAS,
    # and also save the cycles repartition of EAS
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
            energy_placement = profiler.task_placed_energy_aware
            balance_placement = profiler.task_placed_by_load_balancing

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

            hist = placement_hist[version.__name__]
            hist[0].append(energy_placement)
            hist[1].append(balance_placement)

    placement_file_name = f"placement_{cpus_description}.csv"
    _write_placement(placement_hist, placement_file_name)
    diff_file_name = f"diff_{cpus_description}.csv"
    _write_differences(diff_hist, diff_file_name)

    print(f"Ending experiment on: {cpus_description}")


def run_extra_experiment_calibration_on(cpus: list[CPU], cpus_description: str):
    print(f"Stating extra experiment for calibration on: {cpus_description}")

    em: EnergyModel = EnergyModel(cpus)
    load_generators: dict[str, LoadGenerator] = {"EAS": LoadGenerator(
        PICK_DISTRIB_INTS, MAX_DISTRIB_INSTS, CREATE_TASK_PROB, RANDOM_SEED)}

    diff_hist: dict[str, tuple[list[float], list[float],
                               list[float], list[float], list[float]]] = {}

    placement_hist: dict[str, tuple[list[int], list[int]]] = {}

    for count_limit in range(2, int(len(cpus) / 2) + 2):
        version_name = f"EASOverutil{count_limit}cores"
        load_generators[version_name] = LoadGenerator(
            PICK_DISTRIB_INTS, MAX_DISTRIB_INSTS, CREATE_TASK_PROB, RANDOM_SEED)
        diff_hist[version_name] = ([], [], [], [], [])
        placement_hist[version_name] = ([], [])

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

        for count_limit in range(2, int(len(cpus) / 2) + 2):
            version_name = f"EASOverutil{count_limit}cores"

            scheduler = EASOverutilManycores(
                load_generators[version_name], cpus, em, count_limit=count_limit)
            scheduler.run(60000)
            profiler = scheduler.profiler

            power = profiler.total_energy
            task_cycles = profiler.cycles_hist[0]
            energy_cycles = profiler.cycles_hist[1]
            balance_cycles = profiler.cycles_hist[2]
            idle_cycles = profiler.cycles_hist[3]
            energy_placement = profiler.task_placed_energy_aware
            balance_placement = profiler.task_placed_by_load_balancing

            hist = diff_hist[version_name]
            hist[0].append((power / eas_hist[0] - 1) * 100)
            hist[1].append((task_cycles / eas_hist[1] - 1) * 100)
            hist[2].append((energy_cycles / eas_hist[2] - 1) * 100)
            hist[3].append((balance_cycles / eas_hist[3] - 1) * 100)
            hist[4].append((idle_cycles / eas_hist[4] - 1) * 100)

            hist = placement_hist[version_name]
            hist[0].append(energy_placement)
            hist[1].append(balance_placement)

    placement_file_name = f"placement_calibration_{cpus_description}.csv"
    _write_placement(placement_hist, placement_file_name)
    diff_calibration_file_name = f"diff_calibration_{cpus_description}.csv"
    _write_differences(diff_hist, diff_calibration_file_name)

    print(f"Ending extra experiment for calibration on: {cpus_description}")


if __name__ == "__main__":
    start_time = time.time()

    experiment_args: list[tuple[list[CPU], str]] = [
        (CPUGenerator.gen(little=2, middle=2), "2_little_2_middle"),
        (CPUGenerator.gen(little=4, middle=4), "4_little_4_middle"),
        (CPUGenerator.gen(little=8, middle=8), "8_little_8_middle"),
        (CPUGenerator.gen(little=16, middle=16), "16_little_16_middle"),
        (CPUGenerator.gen(little=32, middle=32), "32_little_32_middle"),
        (CPUGenerator.gen(little=16, middle=16, big=16), "16_little_16_middle_16_big"),
        (CPUGenerator.gen(little=32, middle=32, big=32), "32_little_32_middle_32_big")
    ]

    extra_experiment_args: list[tuple[list[CPU], str]] = [
        (CPUGenerator.gen(little=8, middle=8), "8_little_8_middle")
    ]

    processes = []
    for cpus, cpus_description in experiment_args:
        proc = multiprocessing.Process(
            target=run_experiment_on, args=(cpus, cpus_description))
        proc.start()
        processes.append(proc)

    for cpus, cpus_description in extra_experiment_args:
        proc = multiprocessing.Process(
            target=run_extra_experiment_calibration_on, args=(cpus, cpus_description))
        proc.start()
        processes.append(proc)

    for proc in processes:
        proc.join()

    end_time = time.time()
    print("Min. elasped:", (end_time - start_time) / 60)
