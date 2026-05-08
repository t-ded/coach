from typing import Optional

from coach.domain.personal_bests import RunningPersonalBestsSummary
from coach.domain.training_analytics import PaceZones


def _parse_pace_secs(pace_str: str) -> int:
    """Parse 'M:SS/km' to total seconds per km."""
    time_part = pace_str.split('/')[0]
    minutes_str, seconds_str = time_part.split(':')
    return int(minutes_str) * 60 + int(seconds_str)


def _format_pace_secs(secs: int) -> str:
    """Format total seconds per km to 'M:SS/km'."""
    minutes = secs // 60
    seconds = secs % 60
    return f'{minutes}:{seconds:02d}/km'


def build_pace_zones(pb_summary: RunningPersonalBestsSummary) -> Optional[PaceZones]:
    candidates = [
        ('5K', pb_summary.PB_5K, 0),
        ('10K', pb_summary.PB_10K, -13),
        ('Half-Marathon', pb_summary.PB_HALF_MARATHON, -30),
        ('Marathon', pb_summary.PB_MARATHON, -50),
        ('1K', pb_summary.PB_1K, 15),
    ]

    for reference_distance, pb, adjustment in candidates:
        if pb is None:
            continue

        pace_secs = _parse_pace_secs(pb.pace_str)
        ref_secs = pace_secs + adjustment

        easy_secs = ref_secs + 65
        marathon_secs = ref_secs + 40
        threshold_secs = ref_secs + 15
        interval_secs = ref_secs

        return PaceZones(
            reference_distance=reference_distance,
            easy_pace=_format_pace_secs(easy_secs),
            marathon_pace=_format_pace_secs(marathon_secs),
            threshold_pace=_format_pace_secs(threshold_secs),
            interval_pace=_format_pace_secs(interval_secs),
        )

    return None
