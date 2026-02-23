from datetime import UTC
from datetime import datetime

from coach.domain.activity import Activity
from coach.domain.activity import ActivitySource
from coach.domain.activity import BestEffort
from coach.domain.activity import SportType

SAMPLE_RUN = Activity(
    activity_id=1,
    source=ActivitySource.STRAVA,
    source_activity_id=1,

    sport_type=SportType.RUN,
    name='Sample Run',
    description='Sample Run Description',
    notes='Sample Run Notes',

    start_time_utc=datetime(2025, 1, 1, 1, 0, 0, tzinfo=UTC),
    elapsed_time_seconds=3_600,
    moving_time_seconds=3_500,

    distance_meters=10_000.0,
    elevation_gain_meters=120.0,

    average_heart_rate=None,
    max_heart_rate=None,
    average_power_watts=None,

    is_manual=False,
    is_race=False,

    pbs=[BestEffort(name='1K', moving_time_seconds=120)],
)

SAMPLE_RIDE = Activity(
    activity_id=2,
    source=ActivitySource.STRAVA,
    source_activity_id=2,

    sport_type=SportType.RIDE,
    name='Sample Ride',
    description='Sample Ride Description',
    notes='Sample Ride Notes',

    start_time_utc=datetime(2025, 1, 2, 1, 0, 0, tzinfo=UTC),
    elapsed_time_seconds=3_600,
    moving_time_seconds=3_500,

    distance_meters=20_000.0,
    elevation_gain_meters=200.0,

    average_heart_rate=None,
    max_heart_rate=None,
    average_power_watts=None,

    is_manual=False,
    is_race=False,
)
