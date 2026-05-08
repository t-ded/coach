from typing import Optional

from coach.builders.pace_zones import _parse_pace_secs
from coach.domain.activity import SportType
from coach.domain.training_analytics import PaceZones
from coach.domain.training_summaries import ActivitySummary

_INTERVAL_RATIO_THRESHOLD = 0.87
_INTERVAL_MAX_HR_FRACTION = 0.92
_TEMPO_AVG_HR_FRACTION = 0.85
_EASY_AVG_HR_FRACTION = 0.77
_LONG_RUN_ELAPSED_SECONDS = 3900  # 65 minutes


def _activity_pace_secs(activity: ActivitySummary) -> Optional[int]:
    if activity.distance_meters is None or not activity.distance_meters:
        return None
    if activity.moving_time_seconds is None or not activity.moving_time_seconds:
        return None
    return int(activity.moving_time_seconds / (activity.distance_meters / 1000))


def classify_run_workout(
    activity: ActivitySummary,
    max_hr_estimate: Optional[float],
    pace_zones: Optional[PaceZones],
) -> Optional[str]:
    if activity.sport_type != SportType.RUN:
        return None

    moving = activity.moving_time_seconds
    elapsed = activity.elapsed_time_seconds
    avg_hr = activity.average_heart_rate
    max_hr = activity.max_heart_rate

    has_rest = moving is not None and elapsed > 0 and moving / elapsed < _INTERVAL_RATIO_THRESHOLD
    activity_pace = _activity_pace_secs(activity)
    threshold_secs = _parse_pace_secs(pace_zones.threshold_pace) if pace_zones else None

    # Interval — HR-based
    if (
        moving is not None
        and elapsed > 0
        and moving / elapsed < _INTERVAL_RATIO_THRESHOLD
        and max_hr is not None
        and max_hr_estimate is not None
        and max_hr >= max_hr_estimate * _INTERVAL_MAX_HR_FRACTION
    ):
        return 'Interval'

    # Interval — pace-based fallback
    if has_rest and pace_zones is not None and activity_pace is not None and threshold_secs is not None and activity_pace <= threshold_secs + 30:
        return 'Interval'

    # Tempo — HR-based
    if avg_hr is not None and max_hr_estimate is not None and avg_hr >= max_hr_estimate * _TEMPO_AVG_HR_FRACTION:
        return 'Tempo'

    # Tempo — pace-based fallback
    if pace_zones is not None and activity_pace is not None and threshold_secs is not None and activity_pace <= threshold_secs + 20:
        return 'Tempo'

    # Long Run
    if avg_hr is not None and max_hr_estimate is not None and avg_hr <= max_hr_estimate * _EASY_AVG_HR_FRACTION and elapsed >= _LONG_RUN_ELAPSED_SECONDS:
        return 'Long Run'

    # Easy
    if avg_hr is not None and max_hr_estimate is not None and avg_hr <= max_hr_estimate * _EASY_AVG_HR_FRACTION:
        return 'Easy'

    return None
