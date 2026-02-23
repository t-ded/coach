from collections.abc import Iterable

from coach.domain.activity import Activity
from coach.domain.activity import SportType
from coach.domain.personal_bests import RunningPersonalBest
from coach.domain.personal_bests import RunningPersonalBestsSummary


def build_running_personal_bests_summary(activities: Iterable[Activity]) -> RunningPersonalBestsSummary:
    pbs_per_distance: dict[str, RunningPersonalBest] = {}

    for activity in activities:
        if activity.sport_type == SportType.RUN:
            for pb in activity.pbs:
                # Activities are sorted chronologically during loading, hence the last PB per distance is always the actual best one
                pbs_per_distance[pb.name] = RunningPersonalBest.from_running_best_effort(pb, activity_date=activity.start_time_utc)

    return RunningPersonalBestsSummary(
        PB_1K=pbs_per_distance.get('1K'),
        PB_5K=pbs_per_distance.get('5K'),
        PB_10K=pbs_per_distance.get('10K'),
        PB_15K=pbs_per_distance.get('15K'),
        PB_HALF_MARATHON=pbs_per_distance.get('Half-Marathon'),
        PB_MARATHON=pbs_per_distance.get('Marathon'),
    )
