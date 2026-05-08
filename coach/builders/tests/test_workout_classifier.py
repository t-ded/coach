from datetime import UTC
from datetime import date
from datetime import datetime
from typing import Optional

from coach.builders.pace_zones import build_pace_zones
from coach.builders.workout_classifier import classify_run_workout
from coach.domain.activity import SportType
from coach.domain.personal_bests import RunningPersonalBest
from coach.domain.personal_bests import RunningPersonalBestsSummary
from coach.domain.training_analytics import PaceZones
from coach.domain.training_summaries import ActivitySummary

_START = datetime(2025, 1, 1, tzinfo=UTC)


def _make_pace_zones() -> Optional[PaceZones]:
    pb = RunningPersonalBest(achieved_on=date(2025, 1, 1), pace_str='4:00/km')
    return build_pace_zones(
        RunningPersonalBestsSummary(
            PB_1K=None,
            PB_5K=pb,
            PB_10K=None,
            PB_15K=None,
            PB_HALF_MARATHON=None,
            PB_MARATHON=None,
        ),
    )


def _run(
    *,
    elapsed: int = 3000,
    moving: int | None = 3000,
    avg_hr: float | None = None,
    max_hr: float | None = None,
    distance: float | None = 5000.0,
) -> ActivitySummary:
    return ActivitySummary(
        start_time_utc=_START,
        sport_type=SportType.RUN,
        title='Test Run',
        elapsed_time_seconds=elapsed,
        moving_time_seconds=moving,
        distance_meters=distance,
        average_heart_rate=avg_hr,
        max_heart_rate=max_hr,
    )


def _non_run() -> ActivitySummary:
    return ActivitySummary(
        start_time_utc=_START,
        sport_type=SportType.RIDE,
        title='Ride',
        elapsed_time_seconds=3600,
    )


class TestClassifyRunWorkout:
    def test_non_run_returns_none(self) -> None:
        assert classify_run_workout(_non_run(), max_hr_estimate=180.0, pace_zones=None) is None

    def test_run_no_hr_no_pace_zones_returns_none(self) -> None:
        assert classify_run_workout(_run(), max_hr_estimate=None, pace_zones=None) is None

    def test_interval_hr_based(self) -> None:
        # ratio = 2700/3600 = 0.75 < 0.87; max_hr=188 >= 188*0.92=173
        activity = _run(elapsed=3600, moving=2700, max_hr=188.0)
        result = classify_run_workout(activity, max_hr_estimate=188.0, pace_zones=None)
        assert result == 'Interval'

    def test_interval_hr_based_requires_sufficient_max_hr(self) -> None:
        # ratio low but max_hr too low → no interval via HR
        activity = _run(elapsed=3600, moving=2700, max_hr=150.0, avg_hr=140.0)
        result = classify_run_workout(activity, max_hr_estimate=188.0, pace_zones=None)
        # avg_hr 140 <= 188*0.77=144.8, elapsed=3600 < 3900 → Easy
        assert result == 'Easy'

    def test_interval_pace_based_fallback(self) -> None:
        # ratio 0.75 < 0.87; no HR data; fast pace ≤ threshold+30
        # 5K PB 4:00/km → threshold=4:15/km=255 sec/km; threshold+30=285 sec/km
        # moving=2700s, distance=5000m → pace = 2700/(5000/1000) = 540 sec/km → too slow
        # Use a fast pace: distance=7000m, moving=1700s → pace = 1700/7 = 243 sec/km ≤ 285 → Interval
        pace_zones = _make_pace_zones()
        activity = _run(elapsed=2500, moving=1700, distance=7000.0)
        result = classify_run_workout(activity, max_hr_estimate=None, pace_zones=pace_zones)
        assert result == 'Interval'

    def test_tempo_hr_based(self) -> None:
        # avg_hr=165, max_hr_estimate=190 → 165 >= 190*0.85=161.5
        activity = _run(avg_hr=165.0)
        result = classify_run_workout(activity, max_hr_estimate=190.0, pace_zones=None)
        assert result == 'Tempo'

    def test_tempo_pace_based_fallback(self) -> None:
        # No HR; threshold=4:15/km=255 sec/km; threshold+20=275 sec/km
        # distance=5000m, moving=1300s → pace = 1300/5 = 260 sec/km ≤ 275 → Tempo
        pace_zones = _make_pace_zones()
        activity = _run(elapsed=1400, moving=1300, distance=5000.0)
        result = classify_run_workout(activity, max_hr_estimate=None, pace_zones=pace_zones)
        assert result == 'Tempo'

    def test_long_run(self) -> None:
        # avg_hr=140 <= 188*0.77=144.8; elapsed=4200 >= 3900
        activity = _run(elapsed=4200, moving=4200, avg_hr=140.0)
        result = classify_run_workout(activity, max_hr_estimate=188.0, pace_zones=None)
        assert result == 'Long Run'

    def test_easy_run(self) -> None:
        # avg_hr=130 <= 188*0.77=144.8; elapsed=2400 < 3900
        activity = _run(elapsed=2400, moving=2400, avg_hr=130.0)
        result = classify_run_workout(activity, max_hr_estimate=188.0, pace_zones=None)
        assert result == 'Easy'

    def test_slow_pace_with_zones_returns_none_no_hr(self) -> None:
        # Slow pace: distance=5000m, moving=3000s → 600 sec/km; far above threshold zone
        pace_zones = _make_pace_zones()
        activity = _run(elapsed=3000, moving=3000, distance=5000.0)
        result = classify_run_workout(activity, max_hr_estimate=None, pace_zones=pace_zones)
        assert result is None

    def test_strength_activity_returns_none(self) -> None:
        activity = ActivitySummary(
            start_time_utc=_START,
            sport_type=SportType.STRENGTH,
            title='Upper Body',
            elapsed_time_seconds=3600,
        )
        assert classify_run_workout(activity, max_hr_estimate=180.0, pace_zones=None) is None
