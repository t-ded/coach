from coach.persistence.serialization import deserialize_activity
from coach.persistence.serialization import serialize_activity
from coach.tests.utils_for_tests import SAMPLE_RUN


def test_serialize_activity() -> None:
    serialized = serialize_activity(SAMPLE_RUN)

    assert serialized == {
        'activity_id': SAMPLE_RUN.activity_id,
        'source': SAMPLE_RUN.source.value,
        'source_activity_id': SAMPLE_RUN.source_activity_id,

        'sport_type': SAMPLE_RUN.sport_type.value,
        'name': SAMPLE_RUN.name,
        'description': SAMPLE_RUN.description,
        'notes': SAMPLE_RUN.notes,

        'start_time_utc': SAMPLE_RUN.start_time_utc.isoformat(),
        'elapsed_time_seconds': SAMPLE_RUN.elapsed_time_seconds,
        'moving_time_seconds': SAMPLE_RUN.moving_time_seconds,

        'distance_meters': SAMPLE_RUN.distance_meters,
        'elevation_gain_meters': SAMPLE_RUN.elevation_gain_meters,

        'average_heart_rate': SAMPLE_RUN.average_heart_rate,
        'max_heart_rate': SAMPLE_RUN.max_heart_rate,
        'average_power_watts': SAMPLE_RUN.average_power_watts,

        'is_manual': int(SAMPLE_RUN.is_manual),
        'is_race': int(SAMPLE_RUN.is_race),
        'pbs': '[{"name": "1K", "moving_time_seconds": 120}]',
    }


def test_deserialize_activity() -> None:
    deserialized = deserialize_activity(
        {
            'activity_id': SAMPLE_RUN.activity_id,
            'source': SAMPLE_RUN.source.value,
            'source_activity_id': SAMPLE_RUN.source_activity_id,

            'sport_type': SAMPLE_RUN.sport_type.value,
            'name': SAMPLE_RUN.name,
            'description': SAMPLE_RUN.description,
            'notes': SAMPLE_RUN.notes,

            'start_time_utc': SAMPLE_RUN.start_time_utc.isoformat(),
            'elapsed_time_seconds': SAMPLE_RUN.elapsed_time_seconds,
            'moving_time_seconds': SAMPLE_RUN.moving_time_seconds,

            'distance_meters': SAMPLE_RUN.distance_meters,
            'elevation_gain_meters': SAMPLE_RUN.elevation_gain_meters,

            'average_heart_rate': SAMPLE_RUN.average_heart_rate,
            'max_heart_rate': SAMPLE_RUN.max_heart_rate,
            'average_power_watts': SAMPLE_RUN.average_power_watts,

            'is_manual': int(SAMPLE_RUN.is_manual),
            'is_race': int(SAMPLE_RUN.is_race),
            'pbs': '[{"name": "1K", "moving_time_seconds": 120, "activity_date": "2025-01-01T01:00:00+00:00"}]',
        },
    )

    assert deserialized == SAMPLE_RUN
