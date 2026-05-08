from datetime import UTC
from datetime import datetime

from coach.builders.recent_training_history import build_recent_training_history
from coach.builders.training_trends import build_training_trends
from coach.domain.activity import Activity
from coach.domain.activity import SportType
from coach.domain.training_analytics import TrainingTrends


def _build(activities: list[Activity], generated_at: datetime, num_history_weeks: int = 4) -> TrainingTrends:
    history = build_recent_training_history(activities=activities, generated_at=generated_at, num_history_weeks=num_history_weeks)
    return build_training_trends(history)


def _make_run(activity_id: int, start: datetime, distance_meters: float) -> Activity:
    return Activity(
        id=activity_id,
        sport_type=SportType.RUN,
        name=f'Run {activity_id}',
        start_time_utc=start,
        elapsed_time_seconds=3600,
        moving_time_seconds=3600,
        distance_meters=distance_meters,
        is_manual=False,
        is_race=False,
        pbs=[],
    )


class TestBuildTrainingTrendsEmpty:
    def test_empty_history_all_none(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        result = _build([], generated_at, num_history_weeks=0)
        assert result.weekly_entries == ()
        assert result.four_week_avg_running_km is None
        assert result.volume_trend == 'stable'
        assert result.weeks_active == 0
        assert result.longest_run_km is None

    def test_no_activities_with_weeks(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        result = _build([], generated_at, num_history_weeks=4)
        assert len(result.weekly_entries) == 4
        assert result.four_week_avg_running_km is None
        assert result.weeks_active == 0
        assert result.longest_run_km is None


class TestBuildTrainingTrendsSingleWeek:
    def test_single_week_with_running(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        run = _make_run(1, datetime(2025, 3, 10, 8, 0, tzinfo=UTC), 10_000.0)
        result = _build([run], generated_at, num_history_weeks=1)
        assert len(result.weekly_entries) == 1
        assert result.weekly_entries[0].running_km == 10.0
        assert result.volume_trend == 'stable'  # only 1 entry
        assert result.weeks_active == 1
        assert result.longest_run_km == 10.0


class TestBuildTrainingTrendsVolumeTrend:
    def test_increasing_volume_trend(self) -> None:
        # Week 4 (most recent): 60 km; weeks 1-3 avg: 30 km → increasing
        generated_at = datetime(2025, 3, 31, 10, 0, tzinfo=UTC)
        activities = [
            _make_run(1, datetime(2025, 3, 3, 8, 0, tzinfo=UTC), 30_000.0),  # week -4
            _make_run(2, datetime(2025, 3, 10, 8, 0, tzinfo=UTC), 30_000.0),  # week -3
            _make_run(3, datetime(2025, 3, 17, 8, 0, tzinfo=UTC), 30_000.0),  # week -2
            _make_run(4, datetime(2025, 3, 24, 8, 0, tzinfo=UTC), 60_000.0),  # week -1 (most recent)
        ]
        result = _build(activities, generated_at, num_history_weeks=4)
        assert result.volume_trend == 'increasing'

    def test_decreasing_volume_trend(self) -> None:
        # Week 4 (most recent): 15 km; weeks 1-3 avg: 30 km → decreasing
        generated_at = datetime(2025, 3, 31, 10, 0, tzinfo=UTC)
        activities = [
            _make_run(1, datetime(2025, 3, 3, 8, 0, tzinfo=UTC), 30_000.0),
            _make_run(2, datetime(2025, 3, 10, 8, 0, tzinfo=UTC), 30_000.0),
            _make_run(3, datetime(2025, 3, 17, 8, 0, tzinfo=UTC), 30_000.0),
            _make_run(4, datetime(2025, 3, 24, 8, 0, tzinfo=UTC), 15_000.0),
        ]
        result = _build(activities, generated_at, num_history_weeks=4)
        assert result.volume_trend == 'decreasing'

    def test_stable_volume_trend(self) -> None:
        # All weeks ~30 km → stable
        generated_at = datetime(2025, 3, 31, 10, 0, tzinfo=UTC)
        activities = [
            _make_run(1, datetime(2025, 3, 3, 8, 0, tzinfo=UTC), 30_000.0),
            _make_run(2, datetime(2025, 3, 10, 8, 0, tzinfo=UTC), 30_000.0),
            _make_run(3, datetime(2025, 3, 17, 8, 0, tzinfo=UTC), 30_000.0),
            _make_run(4, datetime(2025, 3, 24, 8, 0, tzinfo=UTC), 31_000.0),
        ]
        result = _build(activities, generated_at, num_history_weeks=4)
        assert result.volume_trend == 'stable'


class TestBuildTrainingTrendsLongestRun:
    def test_longest_run_correctly_identified(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        activities = [
            _make_run(1, datetime(2025, 3, 10, 8, 0, tzinfo=UTC), 8_000.0),
            _make_run(2, datetime(2025, 3, 10, 10, 0, tzinfo=UTC), 22_500.0),
            _make_run(3, datetime(2025, 3, 10, 16, 0, tzinfo=UTC), 5_000.0),
        ]
        result = _build(activities, generated_at, num_history_weeks=1)
        assert result.longest_run_km == 22.5

    def test_no_runs_longest_run_is_none(self) -> None:
        generated_at = datetime(2025, 3, 17, 10, 0, tzinfo=UTC)
        strength = Activity(
            id=1,
            sport_type=SportType.STRENGTH,
            name='Weights',
            start_time_utc=datetime(2025, 3, 10, 8, 0, tzinfo=UTC),
            elapsed_time_seconds=3600,
            is_manual=False,
            is_race=False,
            pbs=[],
        )
        result = _build([strength], generated_at, num_history_weeks=1)
        assert result.longest_run_km is None


class TestBuildTrainingTrendsWeeksActive:
    def test_inactive_week_not_counted(self) -> None:
        generated_at = datetime(2025, 3, 31, 10, 0, tzinfo=UTC)
        # Only one of the 4 weeks has an activity
        run = _make_run(1, datetime(2025, 3, 3, 8, 0, tzinfo=UTC), 10_000.0)
        result = _build([run], generated_at, num_history_weeks=4)
        assert result.weeks_active == 1

    def test_all_weeks_active(self) -> None:
        generated_at = datetime(2025, 3, 31, 10, 0, tzinfo=UTC)
        activities = [_make_run(i, datetime(2025, 3, 3 + (i - 1) * 7, 8, 0, tzinfo=UTC), 10_000.0) for i in range(1, 5)]
        result = _build(activities, generated_at, num_history_weeks=4)
        assert result.weeks_active == 4
