from coach.domain.activity import SportType
from coach.domain.goals import DistanceActivityTrainingGoal
from coach.domain.goals import Priority
from coach.domain.goals import TrainingGoal
from coach.persistence.serialization import deserialize_activity
from coach.persistence.serialization import deserialize_goal
from coach.persistence.serialization import serialize_activity
from coach.persistence.serialization import serialize_goal
from coach.tests.utils_for_tests import SAMPLE_RUN


def test_serialize_activity() -> None:
    serialized = serialize_activity(SAMPLE_RUN)

    assert serialized == {
        'id': SAMPLE_RUN.id,
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
        'is_manual': SAMPLE_RUN.is_manual,
        'is_race': SAMPLE_RUN.is_race,
        'pbs': [{'name': '1K', 'moving_time_seconds': 120}],
        'splits': [],
    }


def test_deserialize_activity() -> None:
    deserialized = deserialize_activity(
        {
            'id': SAMPLE_RUN.id,
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
            'is_manual': SAMPLE_RUN.is_manual,
            'is_race': SAMPLE_RUN.is_race,
            'pbs': [{'name': '1K', 'moving_time_seconds': 120, 'activity_date': '2025-01-01T01:00:00+00:00'}],
        },
    )

    assert deserialized == SAMPLE_RUN


SAMPLE_BASE_GOAL = TrainingGoal(
    name='Weekly running',
    sport_type=SportType.RUN,
    goal_date='N/A',
    priority=Priority.LOW,
    notes=None,
)

SAMPLE_DISTANCE_GOAL = DistanceActivityTrainingGoal(
    name='Paris Marathon',
    sport_type=SportType.RUN,
    goal_date='2026-04-15',
    priority=Priority.HIGH,
    notes='Target sub-3h',
    goal_distance_meters=42195.0,
    goal_duration_seconds=10800,
    goal_pace='4:16/km',
)


def test_serialize_base_goal() -> None:
    assert serialize_goal(SAMPLE_BASE_GOAL) == {
        'type': 'base',
        'name': 'Weekly running',
        'sport': 'Run',
        'goal_date': 'N/A',
        'priority': 'LOW',
        'notes': None,
    }


def test_serialize_distance_goal() -> None:
    assert serialize_goal(SAMPLE_DISTANCE_GOAL) == {
        'type': 'distance',
        'name': 'Paris Marathon',
        'sport': 'Run',
        'goal_date': '2026-04-15',
        'priority': 'HIGH',
        'notes': 'Target sub-3h',
        'goal_distance_meters': 42195.0,
        'goal_duration_seconds': 10800,
        'goal_pace': '4:16/km',
    }


def test_deserialize_goal_roundtrip_base() -> None:
    assert deserialize_goal(serialize_goal(SAMPLE_BASE_GOAL)) == SAMPLE_BASE_GOAL


def test_deserialize_goal_roundtrip_distance() -> None:
    assert deserialize_goal(serialize_goal(SAMPLE_DISTANCE_GOAL)) == SAMPLE_DISTANCE_GOAL
