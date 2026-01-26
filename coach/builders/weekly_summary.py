from collections.abc import Iterable
from datetime import date
from datetime import datetime

from coach.builders.utils import bucket_activities_by_weekday
from coach.builders.utils import get_activities_between_dates
from coach.builders.utils import get_categorized_volume
from coach.builders.utils import get_week_start_week_end
from coach.domain.activity import Activity
from coach.domain.training_summaries import WeeklySummary


def build_weekly_summary(activities: Iterable[Activity], generated_at: date | datetime) -> WeeklySummary:
    week_start, week_end = get_week_start_week_end(generated_at)
    activities_within_week = get_activities_between_dates(activities, window_start=week_start, window_end=week_end)
    return WeeklySummary(
        week_start=week_start,
        week_end=week_end,
        volume_by_sport=get_categorized_volume(activities_within_week),
        activity_summaries=bucket_activities_by_weekday(activities_within_week),
    )
