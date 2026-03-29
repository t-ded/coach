from datetime import UTC
from datetime import date
from datetime import datetime
from datetime import timedelta

from coach.domain.activity import BestEffort
from coach.domain.activity import SportType
from coach.domain.goals import DistanceActivityTrainingGoal
from coach.domain.goals import Priority
from coach.domain.goals import TrainingGoal
from coach.domain.personal_bests import RunningPersonalBest
from coach.domain.personal_bests import RunningPersonalBestsSummary
from coach.domain.profile import UserProfile
from coach.domain.training_summaries import ActivitySummary
from coach.domain.training_summaries import ActivityVolume
from coach.domain.training_summaries import RecentTrainingHistory
from coach.domain.training_summaries import WeeklyActivities
from coach.domain.training_summaries import WeeklySummary
from coach.reasoning.coach.context import build_coach_context
from coach.reasoning.coach.sections.personal_bests import PersonalBestsSection
from coach.reasoning.coach.sections.profile import ProfileSection
from coach.reasoning.coach.sections.profile import render_training_goal
from coach.reasoning.coach.sections.training_history import TrainingHistorySection
from coach.tests.utils_for_tests import make_activity


class TestPersonalBestsSection:
    def test_render(self) -> None:
        today = datetime.now(tz=UTC).date()
        pbs = RunningPersonalBestsSummary(
            PB_1K=RunningPersonalBest(achieved_on=today - timedelta(days=1), pace_str='3:30/km'),
            PB_5K=RunningPersonalBest(achieved_on=today - timedelta(days=365), pace_str='4:00/km'),
            PB_10K=None,
            PB_15K=None,
            PB_HALF_MARATHON=RunningPersonalBest(achieved_on=today - timedelta(days=30), pace_str='4:31/km'),
            PB_MARATHON=None,
        )

        section = PersonalBestsSection(pbs)
        result = section.render()
        expected = f"""----------------------------------------
Running personal bests:
- 1K: 3:30/km on {today - timedelta(days=1)} (1 day ago)
- 5K: 4:00/km on {today - timedelta(days=365)} (365 days ago)
- 10K: No PB recorded
- 15K: No PB recorded
- Half Marathon: 4:31/km on {today - timedelta(days=30)} (30 days ago)
- Marathon: No PB recorded
----------------------------------------"""

        assert result == expected


class TestTrainingHistorySection:
    def setup_method(self) -> None:
        placeholder_start_time = datetime(2024, 1, 1, tzinfo=UTC)
        self._weekly_activities: WeeklyActivities = {
            'Monday': [
                ActivitySummary(start_time_utc=placeholder_start_time, sport_type=SportType.RUN, description='Run 1', elapsed_time_seconds=10, distance_meters=100),
                ActivitySummary(start_time_utc=placeholder_start_time, sport_type=SportType.RUN, description='Run 2', elapsed_time_seconds=240, distance_meters=1000),
            ],
            'Tuesday': [],
            'Wednesday': [],
            'Thursday': [],
            'Friday': [
                ActivitySummary(start_time_utc=placeholder_start_time, sport_type=SportType.RIDE, description='Ride 1', elapsed_time_seconds=3600, distance_meters=20_000, elevation_gain_meters=100),
            ],
            'Saturday': [],
            'Sunday': [],
        }
        self._volume_by_sport = {
            SportType.RUN: ActivityVolume(num_activities=2, duration_seconds=250, distance_meters=1_100.0),
            SportType.RIDE: ActivityVolume(num_activities=1, duration_seconds=3600, distance_meters=20_000.0),
        }

    def test_render_single_history_week(self) -> None:
        previous_weekly_summary = WeeklySummary(
            week_start=date(2024, 1, 1),
            week_end=date(2024, 1, 7),
            volume_by_sport=self._volume_by_sport,
            activity_summaries=self._weekly_activities,
        )
        current_weekly_summary = WeeklySummary(
            week_start=date(2024, 1, 8),
            week_end=date(2024, 1, 14),
            volume_by_sport=self._volume_by_sport,
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
- Duration: 00:00:10
- Distance: 0.1 km
- Pace: 1:40/km

Run: Run 2
- Duration: 00:04:00
- Distance: 1.0 km
- Pace: 4:00/km

--- Friday ---
Ride: Ride 1
- Duration: 01:00:00
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
- Duration: 00:00:10
- Distance: 0.1 km
- Pace: 1:40/km

Run: Run 2
- Duration: 00:04:00
- Distance: 1.0 km
- Pace: 4:00/km

--- Friday ---
Ride: Ride 1
- Duration: 01:00:00
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
        history = RecentTrainingHistory(
            generated_at=datetime(2024, 1, 8, 10, 0, 0, tzinfo=UTC),
            current_week_summary=WeeklySummary(
                week_start=date(2024, 1, 8),
                week_end=date(2024, 1, 14),
                volume_by_sport={SportType.STRENGTH: ActivityVolume(num_activities=1, duration_seconds=3600, distance_meters=None)},
                activity_summaries={
                    'Monday': [
                        ActivitySummary(
                            start_time_utc=datetime(2024, 1, 8, 12, tzinfo=UTC),
                            sport_type=SportType.STRENGTH,
                            description='Upper body',
                            elapsed_time_seconds=3_600,
                            distance_meters=None,
                            average_heart_rate=120,
                        ),
                    ],
                    'Tuesday': [],
                    'Wednesday': [],
                    'Thursday': [],
                    'Friday': [],
                    'Saturday': [],
                    'Sunday': [],
                },
            ),
            history_weekly_summaries=(),
        )

        section = TrainingHistorySection(history)
        result = section.render()
        assert result is not None
        assert 'Distance' not in result
        assert 'Pace' not in result
        assert 'WeightTraining: Upper body' in result
        assert '- Duration: 01:00:00' in result
        assert '- Average heart rate: 120 bpm' in result

    def test_render_activity_with_heart_rate(self) -> None:
        history = RecentTrainingHistory(
            generated_at=datetime(2024, 1, 8, 10, 0, 0, tzinfo=UTC),
            current_week_summary=WeeklySummary(
                week_start=date(2024, 1, 8),
                week_end=date(2024, 1, 14),
                volume_by_sport={SportType.RUN: ActivityVolume(num_activities=1, duration_seconds=1805, distance_meters=5000.0)},
                activity_summaries={
                    'Monday': [
                        ActivitySummary(
                            start_time_utc=datetime(2024, 1, 8, 12, tzinfo=UTC),
                            sport_type=SportType.RUN,
                            description='VO2 Max 5x1 @4:30, 1:30 in between',
                            elapsed_time_seconds=1_805,
                            distance_meters=5_000,
                            elevation_gain_meters=5.0,
                            average_heart_rate=165,
                        ),
                    ],
                    'Tuesday': [],
                    'Wednesday': [],
                    'Thursday': [],
                    'Friday': [],
                    'Saturday': [],
                    'Sunday': [],
                },
            ),
            history_weekly_summaries=(),
        )

        section = TrainingHistorySection(history)
        result = section.render()
        assert result is not None
        assert '- Average heart rate: 165 bpm' in result
        assert 'VO2 Max 5x1 @4:30, 1:30 in between' in result

    def test_render_activity_with_max_heart_rate(self) -> None:
        history = RecentTrainingHistory(
            generated_at=datetime(2024, 1, 8, 10, 0, 0, tzinfo=UTC),
            current_week_summary=WeeklySummary(
                week_start=date(2024, 1, 8),
                week_end=date(2024, 1, 14),
                volume_by_sport={SportType.RUN: ActivityVolume(num_activities=1, duration_seconds=1805, distance_meters=5000.0)},
                activity_summaries={
                    'Monday': [
                        ActivitySummary(
                            start_time_utc=datetime(2024, 1, 8, 12, tzinfo=UTC),
                            sport_type=SportType.RUN,
                            description='Tempo run',
                            elapsed_time_seconds=1_805,
                            distance_meters=5_000,
                            average_heart_rate=165,
                            max_heart_rate=185,
                        ),
                    ],
                    'Tuesday': [],
                    'Wednesday': [],
                    'Thursday': [],
                    'Friday': [],
                    'Saturday': [],
                    'Sunday': [],
                },
            ),
            history_weekly_summaries=(),
        )

        section = TrainingHistorySection(history)
        result = section.render()
        assert result is not None
        assert '- Average heart rate: 165 bpm' in result
        assert '- Max heart rate: 185 bpm' in result

    def test_render_activity_with_rest_time(self) -> None:
        history = RecentTrainingHistory(
            generated_at=datetime(2024, 1, 8, 10, 0, 0, tzinfo=UTC),
            current_week_summary=WeeklySummary(
                week_start=date(2024, 1, 8),
                week_end=date(2024, 1, 14),
                volume_by_sport={SportType.RUN: ActivityVolume(num_activities=1, duration_seconds=2400, distance_meters=5000.0)},
                activity_summaries={
                    'Monday': [
                        ActivitySummary(
                            start_time_utc=datetime(2024, 1, 8, 12, tzinfo=UTC),
                            sport_type=SportType.RUN,
                            description='Intervals 5x1km',
                            elapsed_time_seconds=3_000,
                            moving_time_seconds=2_400,
                            distance_meters=5_000,
                        ),
                    ],
                    'Tuesday': [],
                    'Wednesday': [],
                    'Thursday': [],
                    'Friday': [],
                    'Saturday': [],
                    'Sunday': [],
                },
            ),
            history_weekly_summaries=(),
        )

        section = TrainingHistorySection(history)
        result = section.render()
        assert result is not None
        assert '- Active time: 00:40:00' in result
        assert '- Elapsed time: 00:50:00 (rest: 00:10:00)' in result
        assert 'Duration' not in result

    def test_render_continuous_activity_shows_duration(self) -> None:
        history = RecentTrainingHistory(
            generated_at=datetime(2024, 1, 8, 10, 0, 0, tzinfo=UTC),
            current_week_summary=WeeklySummary(
                week_start=date(2024, 1, 8),
                week_end=date(2024, 1, 14),
                volume_by_sport={SportType.RUN: ActivityVolume(num_activities=1, duration_seconds=1800, distance_meters=5000.0)},
                activity_summaries={
                    'Monday': [
                        ActivitySummary(
                            start_time_utc=datetime(2024, 1, 8, 12, tzinfo=UTC),
                            sport_type=SportType.RUN,
                            description='Easy run',
                            elapsed_time_seconds=1_800,
                            moving_time_seconds=1_800,
                            distance_meters=5_000,
                        ),
                    ],
                    'Tuesday': [],
                    'Wednesday': [],
                    'Thursday': [],
                    'Friday': [],
                    'Saturday': [],
                    'Sunday': [],
                },
            ),
            history_weekly_summaries=(),
        )

        section = TrainingHistorySection(history)
        result = section.render()
        assert result is not None
        assert '- Duration: 00:30:00' in result
        assert 'Active time' not in result
        assert 'Elapsed time' not in result


class TestProfileSection:
    def test_render_all_unset(self) -> None:
        section = ProfileSection(UserProfile())
        result = section.render()
        assert result is not None
        assert result.count('(not set)') == 4
        assert '--- Chat preferences ---' not in result

    def test_render_with_fields(self) -> None:
        profile = UserProfile(chat_preferences='Be concise.', training_preferences='Variety is key.')
        section = ProfileSection(profile)
        result = section.render()
        assert result is not None
        assert '--- Training preferences ---\nVariety is key.' in result
        assert '--- Personal information ---\n(not set)' in result
        assert '--- Chat preferences ---' not in result

    def test_render_with_goals(self) -> None:
        goal = TrainingGoal(name='Sub-20 5K', sport_type=SportType.RUN, goal_date='N/A', priority=Priority.HIGH)
        profile = UserProfile(goals=(goal,))
        section = ProfileSection(profile)
        result = section.render()
        assert result is not None
        assert 'Sub-20 5K' in result
        assert '(not set)' not in result.split('--- Goals ---')[1]


class TestRenderTrainingGoal:
    def test_distance_activity_goal(self) -> None:
        today = datetime.now(tz=UTC).date()
        goal_date = today + timedelta(days=10)

        training_goal = DistanceActivityTrainingGoal(
            name='Half-marathon at 1:45:00',
            sport_type=SportType.RUN,
            goal_date=goal_date,
            goal_distance_meters=21_097.5,
            goal_duration_seconds=6_300,
            goal_pace='5:00/km',
            notes='Would like to try for the PB before the race so that I go into the race knowing I can make it',
        )

        result = render_training_goal(training_goal)
        expected = f"""\
- Half-marathon at 1:45:00
    - Sport: Run
    - Goal date: {goal_date} (in 1 week and 3 days)
    - Distance: 21.0975 km
    - Total duration: 01:45:00
    - Pace: 5:00/km
    - Notes: Would like to try for the PB before the race so that I go into the race knowing I can make it
    - Priority: MEDIUM (Options were: ['LOW', 'MEDIUM', 'HIGH', 'VERY HIGH'])"""

        assert result == expected

    def test_weight_training_goal(self) -> None:
        training_goal = TrainingGoal(
            name='Bench 120 kg',
            sport_type=SportType.STRENGTH,
            goal_date='N/A',
        )

        result = render_training_goal(training_goal)
        expected = """\
- Bench 120 kg
    - Sport: WeightTraining
    - Goal date: N/A
    - Priority: MEDIUM (Options were: ['LOW', 'MEDIUM', 'HIGH', 'VERY HIGH'])"""

        assert result == expected


_FIXED_NOW = datetime(2025, 3, 17, 10, 0, 0, tzinfo=UTC)

_SAMPLE_GOAL = TrainingGoal(name='Sub-20 5K', sport_type=SportType.RUN, goal_date='N/A', priority=Priority.HIGH)


class TestBuildCoachContext:
    def test_profile_section_present_when_profile_is_set(self) -> None:
        profile = UserProfile(training_preferences='Run lots of easy miles.')
        result = build_coach_context(profile=profile, activities=[], num_history_weeks=4, generated_at=_FIXED_NOW)
        assert result is not None
        assert 'Run lots of easy miles.' in result

    def test_profile_section_absent_when_no_profile(self) -> None:
        result = build_coach_context(profile=None, activities=[], num_history_weeks=4, generated_at=_FIXED_NOW)
        assert result is not None
        assert 'User profile:' not in result

    def test_pbs_flow_through_from_activities(self) -> None:
        activity = make_activity(id=1, pbs=[BestEffort(name='5K', moving_time_seconds=1200)], start_time_utc=_FIXED_NOW)
        result = build_coach_context(profile=None, activities=[activity], num_history_weeks=4, generated_at=_FIXED_NOW)
        assert result is not None
        assert '5K' in result

    def test_current_week_day_reflects_generated_at(self) -> None:
        monday = datetime(2025, 3, 17, 10, 0, 0, tzinfo=UTC)
        result = build_coach_context(profile=None, activities=[], num_history_weeks=2, generated_at=monday)
        assert result is not None
        assert 'Monday' in result
