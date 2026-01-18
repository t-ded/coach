from datetime import UTC
from datetime import date
from datetime import datetime

from coach.domain.models import ActivityVolume
from coach.domain.models import SportType
from coach.domain.models import TrainingState
from coach.persistence.serialization import deserialize_activity_volume
from coach.persistence.serialization import deserialize_training_state
from coach.persistence.serialization import serialize_activity_volume
from coach.persistence.serialization import serialize_training_state


def test_serialize_activity_volume() -> None:
    serialized = serialize_activity_volume(
        ActivityVolume(
            distance_meters=10_000.0,
            duration_seconds=3_600,
            num_activities=2,
        ),
    )

    assert serialized == {
        'distance_meters': 10_000.0,
        'duration_seconds': 3_600,
        'num_activities': 2,
    }


def test_deserialize_activity_volume() -> None:
    deserialized = deserialize_activity_volume(
        {
            'distance_meters': 10_000.0,
            'duration_seconds': 3_600,
            'num_activities': 2,
        },
    )

    assert deserialized == ActivityVolume(
        distance_meters=10_000.0,
        duration_seconds=3_600,
        num_activities=2,
    )


def test_serialize_training_state() -> None:
    state = TrainingState(
        generated_at=datetime(2025, 1, 1, 12, tzinfo=UTC),
        window_start=date(2024, 1, 1),
        window_end=date(2025, 1, 1),
        volume_by_sport={
            SportType.RUN: ActivityVolume(distance_meters=10_000.0, num_activities=2, duration_seconds=3_600),
        },
        last_activity_date=date(2024, 12, 31),
    )

    serialized = serialize_training_state(state)

    assert serialized == {
        'generated_at': '2025-01-01T12:00:00+00:00',
        'window_start': '2024-01-01',
        'window_end': '2025-01-01',
        'volume_by_sport': '{"Run": {"distance_meters": 10000.0, "duration_seconds": 3600, "num_activities": 2}}',
        'last_activity_date': '2024-12-31',
    }


def test_deserialize_training_state() -> None:
    serialized = {
        'generated_at': '2025-01-01T12:00:00+00:00',
        'window_start': '2024-01-01',
        'window_end': '2025-01-01',
        'volume_by_sport': '{"Run": {"distance_meters": 10000.0, "duration_seconds": 3600, "num_activities": 2}}',
        'last_activity_date': '2024-12-31',
    }

    deserialized = deserialize_training_state(serialized)

    assert deserialized == TrainingState(
        generated_at=datetime(2025, 1, 1, 12, tzinfo=UTC),
        window_start=date(2024, 1, 1),
        window_end=date(2025, 1, 1),
        volume_by_sport={
            SportType.RUN: ActivityVolume(distance_meters=10_000.0, num_activities=2, duration_seconds=3_600),
        },
        last_activity_date=date(2024, 12, 31),
    )
