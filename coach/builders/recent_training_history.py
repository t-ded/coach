from collections.abc import Iterable
from datetime import datetime
from datetime import timedelta

from coach.builders.weekly_summary import build_weekly_summary
from coach.domain.models import Activity
from coach.domain.models import RecentTrainingHistory
from coach.domain.models import WeeklySummary


def build_recent_training_history(activities: Iterable[Activity], *, generated_at: datetime, num_history_weeks: int) -> RecentTrainingHistory:
    current_week_summary = build_weekly_summary(activities, generated_at)

    history_weekly_summaries: list[WeeklySummary] = []
    for week_number in range(1, num_history_weeks + 1):
        center_date = generated_at - timedelta(weeks=week_number)
        history_weekly_summaries.append(build_weekly_summary(activities, center_date))

    return RecentTrainingHistory(
        generated_at=generated_at,
        current_week_summary=current_week_summary,
        history_weekly_summaries=tuple(history_weekly_summaries),
    )
