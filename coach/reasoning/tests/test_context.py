from datetime import UTC
from datetime import date
from datetime import datetime
from datetime import timedelta

from coach.domain.activity import SportType
from coach.domain.goals import DistanceActivityTrainingGoal
from coach.domain.goals import TrainingGoal
from coach.domain.training_summaries import ActivitySummary
from coach.domain.training_summaries import ActivityVolume
from coach.domain.training_summaries import RecentTrainingHistory
from coach.domain.training_summaries import WeeklyActivities
from coach.domain.training_summaries import WeeklySummary
from coach.reasoning.context import render_activity_summary
from coach.reasoning.context import render_activity_volume
from coach.reasoning.context import render_recent_training_history
from coach.reasoning.context import render_system_prompt
from coach.reasoning.context import render_training_goal
from coach.reasoning.context import render_weekly_activities
from coach.reasoning.context import render_weekly_summary


def test_render_activity_volume() -> None:
    volume = ActivityVolume(
        num_activities=5,
        duration_seconds=3600,
        distance_meters=10_000.0,
    )

    result = render_activity_volume(volume)
    expected_result = """
- Num activities: 5
- Total duration: 01:00:00
- Total distance: 10.0 km
"""

    assert result == expected_result.strip()


def test_render_activity_summary() -> None:
    summary = ActivitySummary(
        start_time_utc=datetime(2024, 1, 1, 12, tzinfo=UTC),
        sport_type=SportType.RUN,
        description='VO2 Max 5x1 @4:30, 1:30 in between',

        duration_seconds=1_805,
        distance_meters=5_000,
        elevation_gain_meters=5.0,
    )

    result = render_activity_summary(summary)
    expected_result = """
Run: VO2 Max 5x1 @4:30, 1:30 in between
- Duration: 00:30:05
- Distance: 5.0 km
- Elevation gain: 5.0 meters
"""

    assert result == expected_result.strip()


def test_render_weekly_activities() -> None:
    placeholder_start_time = datetime(2024, 1, 1, tzinfo=UTC)
    weekly_activities: WeeklyActivities = {
        'Monday': [
            ActivitySummary(start_time_utc=placeholder_start_time, sport_type=SportType.RUN, description='Run 1', duration_seconds=10, distance_meters=100),
            ActivitySummary(start_time_utc=placeholder_start_time, sport_type=SportType.RUN, description='Run 2', duration_seconds=240, distance_meters=1000),
        ],
        'Tuesday': [],
        'Wednesday': [],
        'Thursday': [],
        'Friday': [
            ActivitySummary(start_time_utc=placeholder_start_time, sport_type=SportType.RIDE, description='Ride 1', duration_seconds=3600, distance_meters=20_000, elevation_gain_meters=100),
        ],
        'Saturday': [],
        'Sunday': [],
    }

    result = render_weekly_activities(weekly_activities)
    expected_result = """
--- Monday ---
Run: Run 1
- Duration: 00:00:10
- Distance: 0.1 km

Run: Run 2
- Duration: 00:04:00
- Distance: 1.0 km

--- Friday ---
Ride: Ride 1
- Duration: 01:00:00
- Distance: 20.0 km
- Elevation gain: 100 meters
"""

    assert result == expected_result.lstrip()


def test_render_weekly_summary() -> None:
    week_start = date(2024, 1, 1)
    week_end = date(2024, 1, 7)

    volume_by_sport = {
        SportType.RUN: ActivityVolume(
            num_activities=2,
            duration_seconds=250,
            distance_meters=1_100.0,
        ),
        SportType.RIDE: ActivityVolume(
            num_activities=1,
            duration_seconds=3600,
            distance_meters=20_000.0,
        ),
    }

    placeholder_start_time = datetime(2024, 1, 1, tzinfo=UTC)
    weekly_activities: WeeklyActivities = {
        'Monday': [
            ActivitySummary(start_time_utc=placeholder_start_time, sport_type=SportType.RUN, description='Run 1', duration_seconds=10, distance_meters=100),
            ActivitySummary(start_time_utc=placeholder_start_time, sport_type=SportType.RUN, description='Run 2', duration_seconds=240, distance_meters=1000),
        ],
        'Tuesday': [],
        'Wednesday': [],
        'Thursday': [],
        'Friday': [
            ActivitySummary(start_time_utc=placeholder_start_time, sport_type=SportType.RIDE, description='Ride 1', duration_seconds=3600, distance_meters=20_000, elevation_gain_meters=100),
        ],
        'Saturday': [],
        'Sunday': [],
    }

    weekly_summary = WeeklySummary(
        week_start=week_start,
        week_end=week_end,
        volume_by_sport=volume_by_sport,
        activity_summaries=weekly_activities,
    )

    result = render_weekly_summary(weekly_summary)
    expected_result = """
Weekly summary for 2024-01-01 to 2024-01-07:
----- Per-day breakdown -----
--- Monday ---
Run: Run 1
- Duration: 00:00:10
- Distance: 0.1 km

Run: Run 2
- Duration: 00:04:00
- Distance: 1.0 km

--- Friday ---
Ride: Ride 1
- Duration: 01:00:00
- Distance: 20.0 km
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

    assert result == expected_result.lstrip()


def test_render_recent_training_history() -> None:
    previous_week_start = date(2024, 1, 1)
    previous_week_end = date(2024, 1, 7)
    current_week_start = date(2024, 1, 8)
    current_week_end = date(2024, 1, 14)
    generated_at = datetime(2024, 1, 13, 10, 0, 0, tzinfo=UTC)

    volume_by_sport = {
        SportType.RUN: ActivityVolume(
            num_activities=2,
            duration_seconds=250,
            distance_meters=1_100.0,
        ),
        SportType.RIDE: ActivityVolume(
            num_activities=1,
            duration_seconds=3600,
            distance_meters=20_000.0,
        ),
    }

    placeholder_start_time = datetime(2024, 1, 1, tzinfo=UTC)
    weekly_activities: WeeklyActivities = {
        'Monday': [
            ActivitySummary(start_time_utc=placeholder_start_time, sport_type=SportType.RUN, description='Run 1', duration_seconds=10, distance_meters=100),
            ActivitySummary(start_time_utc=placeholder_start_time, sport_type=SportType.RUN, description='Run 2', duration_seconds=240, distance_meters=1000),
        ],
        'Tuesday': [],
        'Wednesday': [],
        'Thursday': [],
        'Friday': [
            ActivitySummary(start_time_utc=placeholder_start_time, sport_type=SportType.RIDE, description='Ride 1', duration_seconds=3600, distance_meters=20_000, elevation_gain_meters=100),
        ],
        'Saturday': [],
        'Sunday': [],
    }

    previous_weekly_summary = WeeklySummary(
        week_start=previous_week_start,
        week_end=previous_week_end,
        volume_by_sport=volume_by_sport,
        activity_summaries=weekly_activities,
    )

    current_weekly_summary = WeeklySummary(
        week_start=current_week_start,
        week_end=current_week_end,
        volume_by_sport=volume_by_sport,
        activity_summaries=weekly_activities,
    )

    recent_training_history = RecentTrainingHistory(
        generated_at=generated_at,
        current_week_summary=current_weekly_summary,
        history_weekly_summaries=(previous_weekly_summary,),
    )

    result = render_recent_training_history(recent_training_history)
    expected_result = """
Summary of recent training history:
----------------------------------------
1 week before current week:
Weekly summary for 2024-01-01 to 2024-01-07:
----- Per-day breakdown -----
--- Monday ---
Run: Run 1
- Duration: 00:00:10
- Distance: 0.1 km

Run: Run 2
- Duration: 00:04:00
- Distance: 1.0 km

--- Friday ---
Ride: Ride 1
- Duration: 01:00:00
- Distance: 20.0 km
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

Run: Run 2
- Duration: 00:04:00
- Distance: 1.0 km

--- Friday ---
Ride: Ride 1
- Duration: 01:00:00
- Distance: 20.0 km
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

    assert result == expected_result.lstrip()


def test_render_training_goal_distance_activity() -> None:
    today = datetime.now(tz=UTC).date()
    goal_date = today + timedelta(days=10)
    goal_date_str = goal_date.strftime('%Y-%m-%d')

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
    expected_result = f"""
- Half-marathon at 1:45:00
    - Sport: Run
    - Goal date: {goal_date_str} (in 10 days)
    - Distance: 21.0975 km
    - Total duration: 01:45:00
    - Pace: 5:00/km
    - Notes: Would like to try for the PB before the race so that I go into the race knowing I can make it
"""

    assert result == expected_result.strip()


def test_render_training_goal_weight_training() -> None:
    training_goal = TrainingGoal(
        name='Bench 120 kg',
        sport_type=SportType.STRENGTH,
        goal_date='N/A',
    )

    result = render_training_goal(training_goal)
    expected_result = """
- Bench 120 kg
    - Sport: WeightTraining
    - Goal date: N/A
"""

    assert result == expected_result.strip()


def test_render_system_prompt() -> None:
    today = datetime.now(tz=UTC).date()
    goal_date = today + timedelta(days=10)
    goal_date_str = goal_date.strftime('%Y-%m-%d')

    system_prompt = f"""# Training Instructions

### Personal history and details:
- 24 years old, roughly 91 kg, 190 cm tall
- Started running in spring 2025

### Goals:
- Half-marathon at 1:45:00
    - Sport: Run
    - Goal date: {goal_date_str}
    - Distance: 21.0975 km
    - Total duration: 01:45:00

- Bench 120 kg
    - Sport: WeightTraining
    - Goal date: N/A"""

    result = render_system_prompt(system_prompt)
    expected_result = f"""# Training Instructions

### Personal history and details:
- 24 years old, roughly 91 kg, 190 cm tall
- Started running in spring 2025

### Goals:
- Half-marathon at 1:45:00
    - Sport: Run
    - Goal date: {goal_date_str} (in 10 days)
    - Distance: 21.0975 km
    - Total duration: 01:45:00
    - Pace: 4:58/km
- Bench 120 kg
    - Sport: WeightTraining
    - Goal date: N/A"""

    assert result == expected_result


def test_render_system_prompt_none() -> None:
    result = render_system_prompt(None)
    assert result is None
