from scheduler import EAS

class EASOverutilDisabled(EAS):
    def _is_over_utilized(self) -> bool:
        return False