from scheduler import EAS

class EASOverutilManycores(EAS):
    def _is_over_utilized(self) -> bool:
        count: int = 0
        count_limit: float = len(self._cpus) / 2
        for cpu in self._cpus:
            if self._compute_load(cpu) > 80:
                count += 1
                if count >= count_limit:
                    return True
        return False