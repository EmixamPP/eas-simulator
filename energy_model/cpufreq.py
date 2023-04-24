from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cpu import CPU

class Schedutil:
    @staticmethod
    def update(cpu: CPU, capacity: int) -> None:
        for pstate in cpu.pstates:
            cpu.pstate = pstate
            if pstate[0] > capacity:
                break
