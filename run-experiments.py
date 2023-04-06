#!/bin/python

import math
import numpy as np

from scheduler import EAS, LoadGenerator, EASOverutilDisabled
from energy_model import Schedutil, EnergyModel
from cpu import CPU, PerfDom, PState
from profiler import Profiler

if __name__ == "__main__":
    # TODO faire la  règle quadratic de l'énergie (voir mémoire)
    cpus: list[CPU] = [
        CPU(PerfDom("lowpower"), [PState((10**9, 50))], "cpu0"),
        CPU(PerfDom("performance"), [PState((3 * 10**9, 50))], "cpu1")
    ]
    em: EnergyModel = EnergyModel(cpus)
    driver: Schedutil = Schedutil(cpus)
    pick_distrib_ints: int = math.floor(0.25 * 10**9)
    max_distrib_insts: int = math.floor(0.5 * 10**9)

    versions: list[type] = [EAS, EASOverutilDisabled]
    # Profier: total_energy, cycles_hist, created_task/ended_task
    versions_hist: dict[type, tuple[list[int], list[tuple[int, int, int, int, int]], list[float]]] = {
        version: ([], [], []) for version in versions}

    for i in range(30):
        for version in versions:
            loadgenerator: LoadGenerator = LoadGenerator(
                pick_distrib_ints, max_distrib_insts, 0.99, i)
            scheduler = version(loadgenerator, cpus, em, driver)
            scheduler.run(60000)

            versions_hist[version][0].append(Profiler.total_energy)
            versions_hist[version][1].append(Profiler.cycles_hist)
            versions_hist[version][2].append(
                Profiler.ended_task/Profiler.created_task*100)

            Profiler.reset()
            for cpu in cpus:
                cpu.restart()

    for version in versions:
        print(version.__name__)
        print("\tenergy: ", np.mean(versions_hist[version][0]))
        print("\tcycles: ", np.mean(versions_hist[version][1], axis=0))
        print("\tterminated: ", np.mean(versions_hist[version][2]), "%")


# répéter l'expérience ?X? fois
#
# faire la somme de l'énergie
# montrer l'energie relative au vanilla EAS (un graph à barre, represantant chaque répititon de l'expérience)
# dire de cb de % en moyenne il a été meilleur ou pire
#
# faire la répartition common/idle/energy/balance en % relative au vinilla EAS (un graph à barre avec niveau)
# dire en moyenne cb de % il a de common+idle en + (meilleur troughput PLEASE)
