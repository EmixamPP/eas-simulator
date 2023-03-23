from cpu import CPU, PerfDom, PState


class EM:
    def __init__(self, cpus: list[CPU]) -> None:
        self._power_table: dict[PerfDom, list[PState]] = {}
        self.perf_domains_name: list[PerfDom] = []
        self._cpus = cpus

        for cpu in cpus:
            perf_domain_name = cpu.type
            if perf_domain_name not in self.perf_domains_name:
                self.perf_domains_name.append(perf_domain_name)
                self._power_table[perf_domain_name] = cpu.pstates

    def compute_energy(self, landscape: dict[CPU, int]) -> int:
        total_energy = 0

        for cpu in self._cpus:
            capacity = landscape[cpu]
            energy = 0

            # assume sorted in increasing order
            for pstate in self._power_table[cpu.type]:
                energy = pstate[1]
                if pstate[0] > capacity:
                    break

            total_energy += energy

        return total_energy
