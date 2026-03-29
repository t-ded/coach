from datetime import UTC
from datetime import date
from datetime import datetime
from datetime import timedelta

from coach.domain.activity import Activity
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
from coach.reasoning.coach.coach import Coach
from coach.reasoning.coach.context import build_coach_context
from coach.reasoning.coach.sections.personal_bests import PersonalBestsSection
from coach.reasoning.coach.sections.profile import ProfileSection
from coach.reasoning.coach.sections.profile import render_training_goal
from coach.reasoning.coach.sections.training_history import TrainingHistorySection
from coach.reasoning.providers import LLMProvider
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


# ── Golden-output test: full prompt as the LLM receives it ──────────────────

# Fixed timestamp: Wednesday 2025-03-12 10:00 UTC
_GOLDEN_NOW = datetime(2025, 3, 12, 10, 0, 0, tzinfo=UTC)

_GOLDEN_PROFILE = UserProfile(
    chat_preferences='Be concise and direct.',
    training_preferences='Prefer polarized training with easy runs and hard workouts.',
    personal_information='30-year-old male, running for 5 years.',
    constraints='Can train max 5 days per week, no morning sessions before 7am.',
    goals=(
        TrainingGoal(
            name='Sub-20 5K',
            sport_type=SportType.RUN,
            goal_date='N/A',
            priority=Priority.HIGH,
            notes='Focus on VO2max intervals.',
        ),
    ),
)

# Monday of the previous week (2025-03-03)
_PREV_WEEK_RUN = Activity(
    id=1,
    sport_type=SportType.RUN,
    name='Easy Run',
    notes='$easy aerobic$',
    start_time_utc=datetime(2025, 3, 3, 8, 0, 0, tzinfo=UTC),
    elapsed_time_seconds=3_000,
    moving_time_seconds=3_000,
    distance_meters=8_000.0,
    elevation_gain_meters=50.0,
    average_heart_rate=140,
    max_heart_rate=155,
    is_manual=False,
    is_race=False,
)

# Wednesday of the previous week (2025-03-05) — interval session with rest
_PREV_WEEK_INTERVAL = Activity(
    id=2,
    sport_type=SportType.RUN,
    name='Intervals',
    notes='$5x1km intervals$',
    start_time_utc=datetime(2025, 3, 5, 17, 0, 0, tzinfo=UTC),
    elapsed_time_seconds=3_600,
    moving_time_seconds=2_700,
    distance_meters=7_000.0,
    elevation_gain_meters=20.0,
    average_heart_rate=170,
    max_heart_rate=188,
    is_manual=False,
    is_race=False,
)

# Thursday of the previous week (2025-03-06) — strength session
_PREV_WEEK_STRENGTH = Activity(
    id=3,
    sport_type=SportType.STRENGTH,
    name='Upper Body',
    notes='$upper body strength$',
    start_time_utc=datetime(2025, 3, 6, 18, 0, 0, tzinfo=UTC),
    elapsed_time_seconds=2_700,
    is_manual=False,
    is_race=False,
)

# Monday of the current week (2025-03-10) — easy run
_CURR_WEEK_RUN = Activity(
    id=4,
    sport_type=SportType.RUN,
    name='Recovery Run',
    notes='$recovery jog$',
    start_time_utc=datetime(2025, 3, 10, 8, 0, 0, tzinfo=UTC),
    elapsed_time_seconds=2_400,
    moving_time_seconds=2_400,
    distance_meters=5_000.0,
    average_heart_rate=130,
    max_heart_rate=142,
    is_manual=False,
    is_race=False,
)

_GOLDEN_ACTIVITIES = [_PREV_WEEK_RUN, _PREV_WEEK_INTERVAL, _PREV_WEEK_STRENGTH, _CURR_WEEK_RUN]


class TestGoldenOutputFullPrompt:
    """One place to see the complete prompt that goes to the LLM."""

    def test_full_prompt(self) -> None:
        coach = Coach(
            provider=LLMProvider.GOOGLE,
            model='test-model',
            profile=_GOLDEN_PROFILE,
            activities=_GOLDEN_ACTIVITIES,
            num_history_weeks=1,
            user_display_name='Alex',
            api_key='fake-key-for-test',
            session_summary='We discussed your upcoming 5K goal and agreed to add one more interval session per week.',
            generated_at=_GOLDEN_NOW,
        )

        result = coach._build_prompt('How should I train this week?')

        expected = """\
System instructions:
You are an AI training coach.

You are given an explicit training summary.
All numeric values are already computed and correct.

Hard Constraints:
- Do NOT recalculate distances, durations, totals, or derived metrics.
- Do NOT infer missing data - base all observations strictly on the provided information.
- Do NOT invent activities, sessions, or metrics.
- If information is insufficient to support a claim, state that explicitly.
- Do NOT unnecessarily restate your instructions in your response - only where absolutely necessary to support your statement.

You MAY:
- Apply general training principles and best practices.
- Propose workout structure and specific routines.
- Recommend short-term and long-term progression strategies.
- Extend recommendations beyond current training volume, provided they are logically grounded in the data and in known research.

Your responsibilities:
- Guide the user toward their stated goal(s) based on their current fitness.
- Evaluate observed training patterns.
- Highlight notable observations or potential risks.
- Suggest high-level focus areas where relevant.
- Remain objective and avoid unsupported assumptions.
- Apply general training principles and best practices such as progressive overload (instead of jumping from 2 runs per week to 4), polarized training etc.
User instructions:
Be concise and direct.
Additional context:
Summary of our previous conversation:
We discussed your upcoming 5K goal and agreed to add one more interval session per week.

User profile:
--- Training preferences ---
Prefer polarized training with easy runs and hard workouts.

--- Personal information ---
30-year-old male, running for 5 years.

--- Constraints ---
Can train max 5 days per week, no morning sessions before 7am.

--- Goals ---
- Sub-20 5K
    - Sport: Run
    - Goal date: N/A
    - Notes: Focus on VO2max intervals.
    - Priority: HIGH (Options were: ['LOW', 'MEDIUM', 'HIGH', 'VERY HIGH'])
Recent weeks training context:
Summary of recent training history:
----------------------------------------
1 week before current week:
Weekly summary for 2025-03-03 to 2025-03-09:
----- Per-day breakdown -----
--- Monday ---
Run: easy aerobic
- Duration: 00:50:00
- Distance: 8.0 km
- Pace: 6:15/km
- Elevation gain: 50.0 meters
- Average heart rate: 140 bpm
- Max heart rate: 155 bpm

--- Wednesday ---
Run: 5x1km intervals
- Active time: 00:45:00
- Elapsed time: 01:00:00 (rest: 00:15:00)
- Distance: 7.0 km
- Pace: 6:25/km
- Elevation gain: 20.0 meters
- Average heart rate: 170 bpm
- Max heart rate: 188 bpm

--- Thursday ---
WeightTraining: upper body strength
- Duration: 00:45:00

----- Volume aggregation by sport -----
--- Run ---
- Num activities: 2
- Total duration: 01:35:00
- Total distance: 15.0 km

--- WeightTraining ---
- Num activities: 1
- Total duration: 00:45:00

----------------------------------------

Current week summary (today is Wednesday):
Weekly summary for 2025-03-10 to 2025-03-16:
----- Per-day breakdown -----
--- Monday ---
Run: recovery jog
- Duration: 00:40:00
- Distance: 5.0 km
- Pace: 8:00/km
- Average heart rate: 130 bpm
- Max heart rate: 142 bpm

----- Volume aggregation by sport -----
--- Run ---
- Num activities: 1
- Total duration: 00:40:00
- Total distance: 5.0 km
Running PBs:
----------------------------------------
Running personal bests:
- 1K: No PB recorded
- 5K: No PB recorded
- 10K: No PB recorded
- 15K: No PB recorded
- Half Marathon: No PB recorded
- Marathon: No PB recorded
----------------------------------------
User question:
How should I train this week?
Your answer: <response>"""

        assert result == expected
