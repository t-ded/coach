from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Optional


class PaceZone(StrEnum):
    Z1_RECOVERY = 'Z1/Recovery'
    Z2_EASY = 'Z2/Easy'
    Z3_TEMPO = 'Z3/Tempo'
    Z4_THRESHOLD = 'Z4/Threshold'
    Z5_VO2MAX = 'Z5/VO2max'


@dataclass(frozen=True, kw_only=True, slots=True)
class ZoneDistribution:
    zone: PaceZone
    distance_meters: float
    time_seconds: int


@dataclass(frozen=True, kw_only=True, slots=True)
class ActivityIntensityProfile:
    activity_id: int
    zone_distribution: list[ZoneDistribution]
    primary_zone: PaceZone
    is_negative_split: Optional[bool]
    hr_drift: Optional[float]
    flags: list[str]
