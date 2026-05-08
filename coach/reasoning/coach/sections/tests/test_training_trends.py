from datetime import date

from coach.domain.training_analytics import TrainingTrends
from coach.domain.training_analytics import WeeklyTrendEntry
from coach.reasoning.coach.sections.training_trends import TrainingTrendsSection


def _make_entry(week_start: date, running_km: float = 0.0, total_duration_hours: float = 0.0, session_count: int = 0) -> WeeklyTrendEntry:
    return WeeklyTrendEntry(
        week_start=week_start,
        running_km=running_km,
        total_duration_hours=total_duration_hours,
        session_count=session_count,
    )


def _make_trends(
    weekly_entries: tuple[WeeklyTrendEntry, ...] = (),
    four_week_avg_running_km: float | None = None,
    volume_trend: str = 'stable',
    weeks_active: int = 0,
    longest_run_km: float | None = None,
) -> TrainingTrends:
    return TrainingTrends(
        weekly_entries=weekly_entries,
        four_week_avg_running_km=four_week_avg_running_km,
        volume_trend=volume_trend,
        weeks_active=weeks_active,
        longest_run_km=longest_run_km,
    )


class TestTrainingTrendsSectionNoEntries:
    def test_no_entries_returns_none(self) -> None:
        section = TrainingTrendsSection(_make_trends())
        assert section.render() is None


class TestTrainingTrendsSectionSingleEntry:
    def test_single_entry_renders_header_and_row(self) -> None:
        entry = _make_entry(date(2025, 3, 10), running_km=10.0, total_duration_hours=1.0, session_count=2)
        trends = _make_trends(
            weekly_entries=(entry,),
            four_week_avg_running_km=10.0,
            volume_trend='stable',
            weeks_active=1,
            longest_run_km=10.0,
        )
        section = TrainingTrendsSection(trends)
        result = section.render()
        assert result is not None
        assert 'Training trends (last 1 week):' in result
        assert 'Week of 2025-03-10: 10.0 km' in result
        assert '4-week avg: 10.0 km/week running' in result
        assert 'Volume trend: stable' in result
        assert 'Active weeks: 1/1' in result
        assert 'Longest run: 10.0 km' in result


class TestTrainingTrendsSectionFullFourWeeks:
    def test_four_week_entry_renders_all_weeks(self) -> None:
        entries = (
            _make_entry(date(2025, 3, 3), running_km=52.3, total_duration_hours=4.2, session_count=3),
            _make_entry(date(2025, 3, 10), running_km=48.1, total_duration_hours=4.0, session_count=4),
            _make_entry(date(2025, 3, 17), running_km=55.7, total_duration_hours=4.8, session_count=4),
            _make_entry(date(2025, 3, 24), running_km=61.2, total_duration_hours=5.1, session_count=5),
        )
        trends = _make_trends(
            weekly_entries=entries,
            four_week_avg_running_km=54.3,
            volume_trend='increasing',
            weeks_active=4,
            longest_run_km=22.5,
        )
        section = TrainingTrendsSection(trends)
        result = section.render()
        assert result is not None
        assert 'Training trends (last 4 weeks):' in result
        assert 'Week of 2025-03-03: 52.3 km' in result
        assert 'Week of 2025-03-24: 61.2 km' in result
        assert '4-week avg: 54.3 km/week running' in result
        assert 'Volume trend: increasing' in result
        assert 'Active weeks: 4/4' in result
        assert 'Longest run: 22.5 km' in result


class TestTrainingTrendsSectionNoRunning:
    def test_no_running_omits_avg_and_trend(self) -> None:
        entry = _make_entry(date(2025, 3, 10), running_km=0.0, total_duration_hours=1.0, session_count=3)
        trends = _make_trends(
            weekly_entries=(entry,),
            four_week_avg_running_km=None,  # no running
            volume_trend='stable',
            weeks_active=1,
            longest_run_km=None,
        )
        section = TrainingTrendsSection(trends)
        result = section.render()
        assert result is not None
        assert '4-week avg' not in result
        assert 'Volume trend' not in result
        assert 'Longest run' not in result


class TestTrainingTrendsSectionNoLongestRun:
    def test_no_longest_run_line_omitted(self) -> None:
        entry = _make_entry(date(2025, 3, 10), running_km=10.0, total_duration_hours=1.0, session_count=2)
        trends = _make_trends(
            weekly_entries=(entry,),
            four_week_avg_running_km=10.0,
            volume_trend='stable',
            weeks_active=1,
            longest_run_km=None,
        )
        section = TrainingTrendsSection(trends)
        result = section.render()
        assert result is not None
        assert 'Longest run' not in result
