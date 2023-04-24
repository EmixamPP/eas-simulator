class Clock:
    def __init__(self) -> None:
        self._time_ms: int = 0
    
    @property
    def time(self) -> int:
        return self._time_ms
    
    def inc_ms(self, time_ms: int) -> None:
        self._time_ms += time_ms