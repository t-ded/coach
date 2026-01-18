from datetime import UTC
from datetime import date
from datetime import datetime

from freezegun import freeze_time

from coach.domain.models import ActivityVolume
from coach.domain.models import SportType
from coach.domain.models import TrainingState
from coach.reasoning.context import render_training_state_for_reasoning


@freeze_time('2024-01-20 15:00:00', tz_offset=0)
def test_render_training_state_basic() -> None:
    training_state = TrainingState(
        generated_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        window_start=date(2024, 1, 1),
        window_end=date(2024, 1, 31),
        volume_by_sport={
            SportType.RUN: ActivityVolume(
                num_activities=5,
                duration_seconds=3600,
                distance_meters=10000.0,
            ),
        },
        last_activity_date=None,
    )

    result = render_training_state_for_reasoning(training_state)

    lines = result.split('\n')
    assert 'Training window: 2024-01-01 to 2024-01-31' in lines[0]
    assert 'Snapshot generated at: 2024-01-15 10:00:00+00:00 (5 days ago)' in lines[1]
    assert 'Current date: 2024-01-20 15:00:00+00:00' in lines[2]
    assert 'Volume by sport:' in lines[3]
    assert '- Run: 5 activities, 60 minutes, 10000 meters' in lines[4]


@freeze_time('2024-01-20 15:00:00', tz_offset=0)
def test_render_training_state_multiple_sports() -> None:
    training_state = TrainingState(
        generated_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        window_start=date(2024, 1, 1),
        window_end=date(2024, 1, 31),
        volume_by_sport={
            SportType.RUN: ActivityVolume(
                num_activities=5,
                duration_seconds=3600,
                distance_meters=10000.0,
            ),
            SportType.RIDE: ActivityVolume(
                num_activities=3,
                duration_seconds=7200,
                distance_meters=50000.0,
            ),
            SportType.SWIM: ActivityVolume(
                num_activities=2,
                duration_seconds=1800,
                distance_meters=2000.0,
            ),
        },
        last_activity_date=date(2024, 1, 14),
    )

    result = render_training_state_for_reasoning(training_state)

    lines = result.split('\n')
    assert 'Volume by sport:' in result
    assert '- Run: 5 activities, 60 minutes, 10000 meters' in result
    assert '- Ride: 3 activities, 120 minutes, 50000 meters' in result
    assert '- Swim: 2 activities, 30 minutes, 2000 meters' in result
    assert 'Last activity date: 2024-01-14 (6 days ago)' in lines[-1]


@freeze_time('2024-01-20 15:00:00', tz_offset=0)
def test_render_training_state_no_distance() -> None:
    training_state = TrainingState(
        generated_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        window_start=date(2024, 1, 1),
        window_end=date(2024, 1, 31),
        volume_by_sport={
            SportType.STRENGTH: ActivityVolume(
                num_activities=4,
                duration_seconds=2400,
                distance_meters=None,
            ),
        },
        last_activity_date=None,
    )

    result = render_training_state_for_reasoning(training_state)

    assert '- WeightTraining: 4 activities, 40 minutes' in result
    assert 'meters' not in result.split('Volume by sport:')[1].split('\n')[1]


@freeze_time('2024-01-20 15:00:00', tz_offset=0)
def test_render_training_state_with_last_activity() -> None:
    training_state = TrainingState(
        generated_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        window_start=date(2024, 1, 1),
        window_end=date(2024, 1, 31),
        volume_by_sport={
            SportType.RUN: ActivityVolume(
                num_activities=1,
                duration_seconds=1800,
                distance_meters=5000.0,
            ),
        },
        last_activity_date=date(2024, 1, 10),
    )

    result = render_training_state_for_reasoning(training_state)

    assert 'Last activity date: 2024-01-10 (10 days ago)' in result


@freeze_time('2024-01-20 15:00:00', tz_offset=0)
def test_render_training_state_empty_volume() -> None:
    training_state = TrainingState(
        generated_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        window_start=date(2024, 1, 1),
        window_end=date(2024, 1, 31),
        volume_by_sport={},
        last_activity_date=None,
    )

    result = render_training_state_for_reasoning(training_state)

    lines = result.split('\n')
    assert 'Training window: 2024-01-01 to 2024-01-31' in lines[0]
    assert 'Volume by sport:' in result
    assert 'Last activity date' not in result
