#!/bin/python
from typing import Any
import math
import numpy as np


from scheduler import EAS, LoadGenerator, EASOverutilDisabled, EASOverutilTwolimits, EASOverutilManycores, EASOverutilTwolimitsManycores, EASCorechoiceNextfit
from energy_model import Schedutil, EnergyModel
from cpu import CPU, CPUGenerator
from profiler import Profiler

if __name__ == "__main__":
    versions: list[type] = [
        EAS, 
        EASOverutilDisabled, 
        EASOverutilTwolimits, 
        EASOverutilManycores, 
        EASOverutilTwolimitsManycores, 
        EASCorechoiceNextfit
    ]

    cpus_list : list[tuple[list[CPU], str]] = [
        (CPUGenerator.gen(little=2, middle=2), "2 little 2 middle"),
        (CPUGenerator.gen(little=4, middle=4), "4 little 4 middle"),
        (CPUGenerator.gen(little=8, middle=8), "8 little 8 middle"),
        (CPUGenerator.gen(little=16, middle=16), "16 little 16 middle"),
        (CPUGenerator.gen(little=32, middle=32), "32 little 32 middle"),
        (CPUGenerator.gen(little=16, middle=16, big=16), "16 little 16 middle 16 big"),
        (CPUGenerator.gen(little=32, middle=32, big=32), "32 little 32 middle 32 big")
    ]

    for cpus, cpus_description in cpus_list:
        print(f"CPUs: {cpus_description}")
        em: EnergyModel = EnergyModel(cpus)
        driver: Schedutil = Schedutil(cpus)

        random_seed: int = 1
        pick_distrib_ints: int = math.floor(0.5 * 10**9)
        max_distrib_insts: int = math.floor(1 * 10**9)
        create_task_prob: float = 0.995
        load_generators: dict[type, LoadGenerator] = {version: LoadGenerator(pick_distrib_ints, max_distrib_insts, create_task_prob, random_seed) for version in versions}

        # perform experiences and store observations
        diff_hist: dict[type, tuple[list[float], list[float], list[float], list[float], list[float], list[float]]] = {version: ([], [], [], [], [], []) for version in versions[1:]}
        for i in range(10):
            print(f"\tRepitition {i}")
            eas_hist = (0, 0, 0, 0, 0, 0)
            for version in versions:
                print(f"\t\t{version.__name__}")
                scheduler = version(load_generators[version], cpus, em, driver)
                scheduler.run(60000)

                power = Profiler.total_energy
                task_cycles = Profiler.cycles_hist[0]
                energy_cycles = Profiler.cycles_hist[1]
                balance_cycles = Profiler.cycles_hist[2]
                idle_cycles = Profiler.cycles_hist[3]
                terminated_task_ratio = Profiler.ended_task / Profiler.created_task * 100

                if version == EAS:
                    eas_hist = (power, task_cycles, energy_cycles, balance_cycles, idle_cycles, terminated_task_ratio)
                else:
                    hist = diff_hist[version]
                    hist[0].append((power / eas_hist[0]  - 1) * 100)
                    hist[1].append((task_cycles / eas_hist[1] - 1) * 100)
                    hist[2].append((energy_cycles / eas_hist[2] - 1) * 100)
                    hist[3].append((balance_cycles / eas_hist[3] - 1) * 100)
                    hist[4].append((idle_cycles / eas_hist[4] - 1) * 100)
                    hist[5].append((terminated_task_ratio / eas_hist[5] - 1) * 100)

                #print(Profiler.created_task, Profiler.ended_task)
                Profiler.reset()
                for candidate in cpus:
                    candidate.restart()

        # compute means and variances of difference history
        diff_mean_var: dict[type, dict[str, tuple[Any, Any]]] = {version: {} for version in versions[1:]}
        for version in versions[1:]:
            mean_var = diff_mean_var[version]
            hist = diff_hist[version]
            mean_var["total_energy"] = (np.mean(hist[0]), np.var(hist[0]))
            mean_var["task"] = (np.mean(hist[1]), np.var(hist[1]))
            mean_var["energy"] = (np.mean(hist[2]), np.var(hist[2]))
            mean_var["balance"] = (np.mean(hist[3]), np.var(hist[3]))
            mean_var["idle"] = (np.mean(hist[4]), np.var(hist[4]))
            mean_var["terminated"] = (np.mean(hist[5]), np.var(hist[5]))

        # output results
        with open(f"results_{cpus_description}.csv".replace(" ", "_"), "w") as f:
            f.write("Version,Energy mean,Energy var,Task cycles mean,Task cycles var,Energy cycles mean,Energy cycles var,Balance cycles mean,Balance cycles var,Idle cycles mean,Idle cycles var,Terminated mean,Terminated var\n")
            for version in versions[1:]:
                mean_var = diff_mean_var[version]
                f.write("{},".format(version.__name__))
                f.write("{},{},".format(np.round(mean_var["total_energy"][0], 2), np.round(mean_var["total_energy"][1], 2)))
                f.write("{},{},".format(np.round(mean_var["task"][0], 2), np.round(mean_var["task"][1], 2)))
                f.write("{},{},".format(np.round(mean_var["energy"][0], 2), np.round(mean_var["energy"][1], 2)))
                f.write("{},{},".format(np.round(mean_var["balance"][0], 2), np.round(mean_var["balance"][1], 2)))
                f.write("{},{},".format(np.round(mean_var["idle"][0], 2), np.round(mean_var["idle"][1], 2)))
                f.write("{},{}\n".format(np.round(mean_var["terminated"][0], 2), np.round(mean_var["terminated"][1], 2)))

