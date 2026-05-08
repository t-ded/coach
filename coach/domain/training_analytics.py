from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Optional


@dataclass(frozen=True, kw_only=True, slots=True)
class WeeklyTrendEntry:
    week_start: date
    running_km: float
    total_duration_hours: float
    session_count: int


@dataclass(frozen=True, kw_only=True, slots=True)
class TrainingTrends:
    weekly_entries: tuple[WeeklyTrendEntry, ...]  # oldest first
    four_week_avg_running_km: Optional[float]  # None if no running in period
    volume_trend: str  # 'increasing', 'stable', 'decreasing'
    weeks_active: int  # weeks with >= 1 session, out of len(weekly_entries)
    longest_run_km: Optional[float]  # longest single run across all entries


class TrainingMacroPhase(StrEnum):
    BASE = 'Base building'
    BUILD = 'Build / specificity'
    PEAK = 'Peak'
    TAPER = 'Taper'
    RACE_WEEK = 'Race week'
    OPEN = 'Open training'


@dataclass(frozen=True, kw_only=True, slots=True)
class ActiveTrainingPhase:
    phase: TrainingMacroPhase
    weeks_to_goal: Optional[int]
    goal_name: Optional[str]


@dataclass(frozen=True, kw_only=True, slots=True)
class PaceZones:
    reference_distance: str  # e.g. '5K', '10K'
    easy_pace: str  # 'M:SS/km'
    marathon_pace: str
    threshold_pace: str
    interval_pace: str
