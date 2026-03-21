from datetime import UTC
from datetime import datetime

import pytest

from coach.builders.personal_bests import build_running_personal_bests_summary
from coach.domain.activity import BestEffort
from coach.domain.activity import SportType
from coach.domain.personal_bests import RunningPersonalBest
from coach.tests.utils_for_tests import make_activity


class TestBuildRunningPersonalBestsSummary:
    def test_no_activities_returns_all_none(self) -> None:
        result = build_running_personal_bests_summary([])
        assert result.PB_1K is None
        assert result.PB_5K is None
        assert result.PB_10K is None
        assert result.PB_15K is None
        assert result.PB_HALF_MARATHON is None
        assert result.PB_MARATHON is None

    def test_non_run_activities_are_ignored(self) -> None:
        ride = make_activity(sport_type=SportType.RIDE, pbs=[BestEffort(name='5K', moving_time_seconds=1200)])
        result = build_running_personal_bests_summary([ride])
        assert result.PB_5K is None

    def test_run_with_known_pb_is_captured(self) -> None:
        run = make_activity(pbs=[BestEffort(name='5K', moving_time_seconds=1200)])
        result = build_running_personal_bests_summary([run])
        assert result.PB_5K is not None

    def test_unknown_pb_name_is_ignored(self) -> None:
        run = make_activity(pbs=[BestEffort(name='2K', moving_time_seconds=400)])
        result = build_running_personal_bests_summary([run])
        assert result.PB_1K is None
        assert result.PB_5K is None

    def test_last_pb_per_distance_wins(self) -> None:
        earlier = make_activity(id=1, pbs=[BestEffort(name='5K', moving_time_seconds=1200)], start_time_utc=datetime(2025, 1, 1, tzinfo=UTC))
        later = make_activity(id=2, pbs=[BestEffort(name='5K', moving_time_seconds=1100)], start_time_utc=datetime(2025, 6, 1, tzinfo=UTC))
        result = build_running_personal_bests_summary([earlier, later])
        assert result.PB_5K is not None
        assert result.PB_5K.DATE == later.start_time_utc.date()  # noqa: SIM300

    def test_all_known_distances_are_populated(self) -> None:
        run = make_activity(pbs=[
            BestEffort(name='1K', moving_time_seconds=240),
            BestEffort(name='5K', moving_time_seconds=1200),
            BestEffort(name='10K', moving_time_seconds=2500),
            BestEffort(name='15K', moving_time_seconds=3900),
            BestEffort(name='Half-Marathon', moving_time_seconds=5400),
            BestEffort(name='Marathon', moving_time_seconds=11000),
        ])
        result = build_running_personal_bests_summary([run])
        assert result.PB_1K is not None
        assert result.PB_5K is not None
        assert result.PB_10K is not None
        assert result.PB_15K is not None
        assert result.PB_HALF_MARATHON is not None
        assert result.PB_MARATHON is not None

    def test_pb_date_matches_activity_date(self) -> None:
        start = datetime(2025, 3, 15, tzinfo=UTC)
        run = make_activity(pbs=[BestEffort(name='10K', moving_time_seconds=2500)], start_time_utc=start)
        result = build_running_personal_bests_summary([run])
        assert result.PB_10K is not None
        assert result.PB_10K.DATE == start.date()  # noqa: SIM300


class TestRunningPersonalBestFromBestEffort:
    def test_computes_pace(self) -> None:
        effort = BestEffort(name='5K', moving_time_seconds=1200)
        pb = RunningPersonalBest.from_running_best_effort(effort, activity_date=datetime(2025, 1, 1, tzinfo=UTC).date())
        assert '4:00' in pb.PACE_STR  # 1200s / 5km = 4:00/km

    def test_raises_for_unknown_name(self) -> None:
        with pytest.raises(ValueError, match='not valid running best effort'):
            RunningPersonalBest.from_running_best_effort(
                BestEffort(name='2K', moving_time_seconds=400),
                activity_date=datetime(2025, 1, 1, tzinfo=UTC).date(),
            )
