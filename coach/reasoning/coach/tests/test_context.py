from datetime import UTC
from datetime import datetime
from typing import Optional

from coach.builders.personal_bests import build_running_personal_bests_summary
from coach.builders.recent_training_history import build_recent_training_history
from coach.domain.activity import Activity
from coach.domain.activity import BestEffort
from coach.domain.activity import SportType
from coach.domain.goals import Priority
from coach.domain.goals import TrainingGoal
from coach.domain.profile import UserProfile
from coach.reasoning.coach.coach import Coach
from coach.reasoning.coach.context import build_coach_context
from coach.reasoning.providers import LLMProvider
from coach.tests.utils_for_tests import make_activity

_FIXED_NOW = datetime(2025, 3, 17, 10, 0, 0, tzinfo=UTC)


def _build_context(
    *,
    profile: Optional[UserProfile] = None,
    activities: Optional[list[Activity]] = None,
    num_history_weeks: int = 4,
    generated_at: datetime = _FIXED_NOW,
) -> Optional[str]:
    acts = activities or []
    return build_coach_context(
        profile=profile,
        recent_training_history=build_recent_training_history(activities=acts, generated_at=generated_at, num_history_weeks=num_history_weeks),
        pb_summary=build_running_personal_bests_summary(activities=acts),
    )


class TestBuildCoachContext:
    def test_profile_section_present_when_profile_is_set(self) -> None:
        profile = UserProfile(training_preferences='Run lots of easy miles.')
        result = _build_context(profile=profile)
        assert result is not None
        assert 'Run lots of easy miles.' in result

    def test_profile_section_absent_when_no_profile(self) -> None:
        result = _build_context()
        assert result is not None
        assert 'User profile:' not in result

    def test_pbs_flow_through_from_activities(self) -> None:
        activity = make_activity(id=1, pbs=[BestEffort(name='5K', moving_time_seconds=1200)], start_time_utc=_FIXED_NOW)
        result = _build_context(activities=[activity])
        assert result is not None
        assert '5K' in result

    def test_current_week_day_reflects_generated_at(self) -> None:
        monday = datetime(2025, 3, 17, 10, 0, 0, tzinfo=UTC)
        result = _build_context(generated_at=monday, num_history_weeks=2)
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


def _make_coach(session_summary: Optional[str] = None) -> Coach:
    return Coach(
        provider=LLMProvider.GOOGLE,
        model='test-model',
        profile=_GOLDEN_PROFILE,
        activities=_GOLDEN_ACTIVITIES,
        num_history_weeks=1,
        user_display_name='Alex',
        api_key='fake-key-for-test',
        generated_at=_GOLDEN_NOW,
        session_summary=session_summary,
    )


class TestGoldenOutputFullPrompt:
    """One place to see the complete prompt that goes to the LLM."""

    def test_full_prompt(self) -> None:
        coach = _make_coach(
            session_summary='We discussed your upcoming 5K goal and agreed to add one more interval session per week.',
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

All dates and timestamps in the context are accurate and reflect the actual current date. Use them for all temporal reasoning — do not rely on your training-data knowledge for the current date.
User instructions:
Be concise and direct.
Additional context:
Today's date: Wednesday, March 12, 2025
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
Run: Easy Run
- Moving time: 00:50:00 (no rest)
- Distance: 8.0 km
- Pace: 6:15/km
- Elevation gain: 50.0 meters
- Average heart rate: 140 bpm
- Max heart rate: 155 bpm
- Notes: easy aerobic

--- Wednesday ---
Run: Intervals
- Active time: 00:45:00
- Elapsed time: 01:00:00 (rest: 00:15:00)
- Distance: 7.0 km
- Active pace: 6:25/km
- Elapsed pace: 8:34/km
- Elevation gain: 20.0 meters
- Average heart rate: 170 bpm
- Max heart rate: 188 bpm
- Notes: 5x1km intervals

--- Thursday ---
WeightTraining: Upper Body
- Moving time: 00:45:00 (no rest)
- Notes: upper body strength

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
Run: Recovery Run
- Moving time: 00:40:00 (no rest)
- Distance: 5.0 km
- Pace: 8:00/km
- Average heart rate: 130 bpm
- Max heart rate: 142 bpm
- Notes: recovery jog

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
Conversation so far:
Summary of our previous conversation:
We discussed your upcoming 5K goal and agreed to add one more interval session per week.
User question:
How should I train this week?
Your answer: <response>"""

        assert result == expected


class TestSessionSummary:
    def test_session_summary_present(self) -> None:
        summary_text = 'We talked about increasing weekly mileage gradually.'
        coach = _make_coach(session_summary=summary_text)

        result = coach._build_prompt('What next?')

        assert 'Summary of our previous conversation:' in result
        assert summary_text in result

    def test_session_summary_absent(self) -> None:
        coach = _make_coach(session_summary=None)

        result = coach._build_prompt('What next?')

        assert 'Summary of our previous conversation:' not in result
