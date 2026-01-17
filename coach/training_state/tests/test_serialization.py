from datetime import UTC
from datetime import date
from datetime import datetime

from coach.domain.models import SportType
from coach.training_state.serialization import serialize_training_state
from coach.training_state.training_state import ActivityVolume
from coach.training_state.training_state import TrainingState


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
        'generated_at': datetime(2025, 1, 1, 12, tzinfo=UTC),
        'window_start': date(2024, 1, 1),
        'window_end': date(2025, 1, 1),
        'volume_by_sport': {
            'Run': {'distance_meters': 10_000.0, 'num_activities': 2, 'duration_seconds': 3_600}
        },
        'last_activity_date': date(2024, 12, 31),
    }
