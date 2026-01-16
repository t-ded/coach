from datetime import UTC
from datetime import datetime

from coach.domain.models import Activity
from coach.domain.models import ActivitySource
from coach.domain.models import SportType


SAMPLE_RUN = Activity(
    activity_id=1,
    source=ActivitySource.STRAVA,
    source_activity_id=1,

    sport_type=SportType.RUN,
    name='Sample Run',

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
)

SAMPLE_RIDE = Activity(
    activity_id=2,
    source=ActivitySource.STRAVA,
    source_activity_id=2,

    sport_type=SportType.RIDE,
    name='Sample Ride',

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
