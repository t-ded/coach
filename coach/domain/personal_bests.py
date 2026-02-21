from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

RUNNING_PBS_METERS_MAPPING: dict[str, float] = {
    '1K': 1_000.0,
    '5K': 5_000.0,
    '10K': 10_000.0,
    '15K': 15_000.0,
    'Half-Marathon': 21_097.5,
    'Marathon': 42_195.0,
}


@dataclass(frozen=True, kw_only=True, slots=True)
class RunningPersonalBest:
    DATE: date
    PACE_STR: str


@dataclass(frozen=True, kw_only=True, slots=True)
class RunningPersonalBestsSummary:
    PB_1K: Optional[RunningPersonalBest]
    PB_5K: Optional[RunningPersonalBest]
    PB_10K: Optional[RunningPersonalBest]
    PB_15K: Optional[RunningPersonalBest]
    PB_HALF_MARATHON: Optional[RunningPersonalBest]
    PB_MARATHON: Optional[RunningPersonalBest]

    @classmethod
    def from_pbs(cls, pbs: dict[str, RunningPersonalBest]) -> RunningPersonalBestsSummary:
        return RunningPersonalBestsSummary(
            PB_1K=pbs.get('1K'),
            PB_5K=pbs.get('5K'),
            PB_10K=pbs.get('10K'),
            PB_15K=pbs.get('15K'),
            PB_HALF_MARATHON=pbs.get('Half-Marathon'),
            PB_MARATHON=pbs.get('Marathon'),
        )
