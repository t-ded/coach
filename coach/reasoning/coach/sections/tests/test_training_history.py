from datetime import UTC
from datetime import date
from datetime import datetime

from coach.domain.activity import SportType
from coach.domain.training_summaries import ActivitySummary
from coach.domain.training_summaries import ActivityVolume
from coach.domain.training_summaries import RecentTrainingHistory
from coach.domain.training_summaries import WeeklyActivities
from coach.domain.training_summaries import WeeklySummary
from coach.reasoning.coach.sections.training_history import TrainingHistorySection

_PLACEHOLDER_START = datetime(2024, 1, 1, tzinfo=UTC)


def _make_current_week_history(
    activity_summaries: WeeklyActivities,
    volume_by_sport: dict[SportType, ActivityVolume],
    generated_at: datetime = datetime(2024, 1, 8, 10, 0, 0, tzinfo=UTC),
) -> RecentTrainingHistory:
    return RecentTrainingHistory(
        generated_at=generated_at,
        current_week_summary=WeeklySummary(
            week_start=date(2024, 1, 8),
            week_end=date(2024, 1, 14),
            volume_by_sport=volume_by_sport,
            activity_summaries=activity_summaries,
        ),
        history_weekly_summaries=(),
    )


class TestTrainingHistorySection:
    def setup_method(self) -> None:
        self._weekly_activities: WeeklyActivities = {
            'Monday': [],
            'Tuesday': [],
            'Wednesday': [],
            'Thursday': [],
            'Friday': [],
            'Saturday': [],
            'Sunday': [],
        }

    def test_render_single_history_week(self) -> None:
        self._weekly_activities['Monday'] = [
            ActivitySummary(start_time_utc=_PLACEHOLDER_START, sport_type=SportType.RUN, title='Run 1', elapsed_time_seconds=10, distance_meters=100),
            ActivitySummary(start_time_utc=_PLACEHOLDER_START, sport_type=SportType.RUN, title='Run 2', elapsed_time_seconds=240, distance_meters=1000),
        ]
        self._weekly_activities['Friday'] = [
            ActivitySummary(start_time_utc=_PLACEHOLDER_START, sport_type=SportType.RIDE, title='Ride 1', elapsed_time_seconds=3600, distance_meters=20_000, elevation_gain_meters=100),
        ]
        volume_by_sport = {
            SportType.RUN: ActivityVolume(num_activities=2, duration_seconds=250, distance_meters=1_100.0),
            SportType.RIDE: ActivityVolume(num_activities=1, duration_seconds=3600, distance_meters=20_000.0),
        }
        previous_weekly_summary = WeeklySummary(
            week_start=date(2024, 1, 1),
            week_end=date(2024, 1, 7),
            volume_by_sport=volume_by_sport,
            activity_summaries=self._weekly_activities,
        )
        current_weekly_summary = WeeklySummary(
            week_start=date(2024, 1, 8),
            week_end=date(2024, 1, 14),
            volume_by_sport=volume_by_sport,
            activity_summaries=self._weekly_activities,
        )
        history = RecentTrainingHistory(
            generated_at=datetime(2024, 1, 13, 10, 0, 0, tzinfo=UTC),
            current_week_summary=current_weekly_summary,
            history_weekly_summaries=(previous_weekly_summary,),
        )

        section = TrainingHistorySection(history)
        result = section.render()
        expected = """\
Summary of recent training history:
----------------------------------------
1 week before current week:
Weekly summary for 2024-01-01 to 2024-01-07:
----- Per-day breakdown -----
--- Monday ---
Run: Run 1
- Moving time: 00:00:10 (no rest)
- Distance: 0.1 km
- Pace: 1:40/km

Run: Run 2
- Moving time: 00:04:00 (no rest)
- Distance: 1.0 km
- Pace: 4:00/km

--- Friday ---
Ride: Ride 1
- Moving time: 01:00:00 (no rest)
- Distance: 20.0 km
- Pace: 3:00/km
- Elevation gain: 100 meters

----- Volume aggregation by sport -----
--- Run ---
- Num activities: 2
- Total duration: 00:04:10
- Total distance: 1.1 km

--- Ride ---
- Num activities: 1
- Total duration: 01:00:00
- Total distance: 20.0 km

----------------------------------------

Current week summary (today is Saturday):
Weekly summary for 2024-01-08 to 2024-01-14:
----- Per-day breakdown -----
--- Monday ---
Run: Run 1
- Moving time: 00:00:10 (no rest)
- Distance: 0.1 km
- Pace: 1:40/km

Run: Run 2
- Moving time: 00:04:00 (no rest)
- Distance: 1.0 km
- Pace: 4:00/km

--- Friday ---
Ride: Ride 1
- Moving time: 01:00:00 (no rest)
- Distance: 20.0 km
- Pace: 3:00/km
- Elevation gain: 100 meters

----- Volume aggregation by sport -----
--- Run ---
- Num activities: 2
- Total duration: 00:04:10
- Total distance: 1.1 km

--- Ride ---
- Num activities: 1
- Total duration: 01:00:00
- Total distance: 20.0 km
"""

        assert result == expected

    def test_render_non_distance_activity_omits_distance_and_pace(self) -> None:
        self._weekly_activities['Monday'] = [
            ActivitySummary(
                start_time_utc=datetime(2024, 1, 8, 12, tzinfo=UTC),
                sport_type=SportType.STRENGTH,
                title='Upper body',
                elapsed_time_seconds=3_600,
                distance_meters=None,
                average_heart_rate=120,
            ),
        ]
        volume = {SportType.STRENGTH: ActivityVolume(num_activities=1, duration_seconds=3600, distance_meters=None)}
        history = _make_current_week_history(self._weekly_activities, volume)

        section = TrainingHistorySection(history)
        result = section.render()
        assert result is not None
        assert 'Distance' not in result
        assert 'Pace' not in result
        assert 'WeightTraining: Upper body' in result
        assert '- Moving time: 01:00:00 (no rest)' in result
        assert '- Average heart rate: 120 bpm' in result

    def test_render_activity_with_heart_rate(self) -> None:
        self._weekly_activities['Monday'] = [
            ActivitySummary(
                start_time_utc=datetime(2024, 1, 8, 12, tzinfo=UTC),
                sport_type=SportType.RUN,
                title='VO2 Max 5x1 @4:30, 1:30 in between',
                elapsed_time_seconds=1_805,
                distance_meters=5_000,
                elevation_gain_meters=5.0,
                average_heart_rate=165,
            ),
        ]
        volume = {SportType.RUN: ActivityVolume(num_activities=1, duration_seconds=1805, distance_meters=5000.0)}
        history = _make_current_week_history(self._weekly_activities, volume)

        section = TrainingHistorySection(history)
        result = section.render()
        assert result is not None
        assert '- Average heart rate: 165 bpm' in result
        assert 'VO2 Max 5x1 @4:30, 1:30 in between' in result

    def test_render_activity_with_max_heart_rate(self) -> None:
        self._weekly_activities['Monday'] = [
            ActivitySummary(
                start_time_utc=datetime(2024, 1, 8, 12, tzinfo=UTC),
                sport_type=SportType.RUN,
                title='Tempo run',
                elapsed_time_seconds=1_805,
                distance_meters=5_000,
                average_heart_rate=165,
                max_heart_rate=185,
            ),
        ]
        volume = {SportType.RUN: ActivityVolume(num_activities=1, duration_seconds=1805, distance_meters=5000.0)}
        history = _make_current_week_history(self._weekly_activities, volume)

        section = TrainingHistorySection(history)
        result = section.render()
        assert result is not None
        assert '- Average heart rate: 165 bpm' in result
        assert '- Max heart rate: 185 bpm' in result

    def test_render_activity_with_rest_time(self) -> None:
        self._weekly_activities['Monday'] = [
            ActivitySummary(
                start_time_utc=datetime(2024, 1, 8, 12, tzinfo=UTC),
                sport_type=SportType.RUN,
                title='Intervals 5x1km',
                elapsed_time_seconds=3_000,
                moving_time_seconds=2_400,
                distance_meters=5_000,
            ),
        ]
        volume = {SportType.RUN: ActivityVolume(num_activities=1, duration_seconds=2400, distance_meters=5000.0)}
        history = _make_current_week_history(self._weekly_activities, volume)

        section = TrainingHistorySection(history)
        result = section.render()
        assert result is not None
        assert '- Active time: 00:40:00' in result
        assert '- Elapsed time: 00:50:00 (rest: 00:10:00)' in result
        assert '- Active pace: 8:00/km' in result
        assert '- Elapsed pace: 10:00/km' in result
        assert 'Moving time' not in result

    def test_render_continuous_activity_shows_moving_time(self) -> None:
        self._weekly_activities['Monday'] = [
            ActivitySummary(
                start_time_utc=datetime(2024, 1, 8, 12, tzinfo=UTC),
                sport_type=SportType.RUN,
                title='Easy run',
                elapsed_time_seconds=1_800,
                moving_time_seconds=1_800,
                distance_meters=5_000,
            ),
        ]
        volume = {SportType.RUN: ActivityVolume(num_activities=1, duration_seconds=1800, distance_meters=5000.0)}
        history = _make_current_week_history(self._weekly_activities, volume)

        section = TrainingHistorySection(history)
        result = section.render()
        assert result is not None
        assert '- Moving time: 00:30:00 (no rest)' in result
        assert '- Pace: 6:00/km' in result
        assert 'Active time' not in result
        assert 'Elapsed time' not in result
        assert 'Active pace' not in result
