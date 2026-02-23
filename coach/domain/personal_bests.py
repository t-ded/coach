from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from coach.builders.utils import compute_distance_duration_pace
from coach.domain.activity import BestEffort

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

    @classmethod
    def from_running_best_effort(cls, running_best_effort: BestEffort, *, activity_date: date) -> RunningPersonalBest:
        if running_best_effort.name not in RUNNING_PBS_METERS_MAPPING:
            raise ValueError('Input best effort is not valid running best effort')

        distance_meters = RUNNING_PBS_METERS_MAPPING[running_best_effort.name]
        pace_str = compute_distance_duration_pace(distance_meters=distance_meters, duration_seconds=running_best_effort.moving_time_seconds, pace_str=None).pace_str
        return cls(
            DATE=activity_date,
            PACE_STR=pace_str,
        )


@dataclass(frozen=True, kw_only=True, slots=True)
class RunningPersonalBestsSummary:
    PB_1K: Optional[RunningPersonalBest]
    PB_5K: Optional[RunningPersonalBest]
    PB_10K: Optional[RunningPersonalBest]
    PB_15K: Optional[RunningPersonalBest]
    PB_HALF_MARATHON: Optional[RunningPersonalBest]
    PB_MARATHON: Optional[RunningPersonalBest]
