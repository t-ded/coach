from datetime import UTC
from datetime import datetime
from typing import Optional

from coach.domain.activity import Activity
from coach.domain.activity import BestEffort
from coach.domain.activity import Split
from coach.domain.activity import SportType

_DEFAULT_START = datetime(2025, 1, 1, tzinfo=UTC)


def make_activity(
    *,
    id: int = 1,  # noqa: A002
    sport_type: SportType = SportType.RUN,
    start_time_utc: datetime = _DEFAULT_START,
    pbs: Optional[list[BestEffort]] = None,
    splits: Optional[list[Split]] = None,
) -> Activity:
    return Activity(
        id=id,
        sport_type=sport_type,
        name=None,
        start_time_utc=start_time_utc,
        elapsed_time_seconds=3_600,
        is_manual=False,
        is_race=False,
        pbs=pbs or [],
        splits=splits or [],
    )


SAMPLE_RUN = Activity(
    id=1,
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
    is_manual=False,
    is_race=False,
    pbs=[BestEffort(name='1K', moving_time_seconds=120)],
)

SAMPLE_RIDE = Activity(
    id=2,
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
    is_manual=False,
    is_race=False,
)
