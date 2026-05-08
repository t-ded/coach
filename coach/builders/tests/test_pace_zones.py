from datetime import date

from coach.builders.pace_zones import _format_pace_secs
from coach.builders.pace_zones import _parse_pace_secs
from coach.builders.pace_zones import build_pace_zones
from coach.domain.personal_bests import RunningPersonalBest
from coach.domain.personal_bests import RunningPersonalBestsSummary

_NO_PBS = RunningPersonalBestsSummary(
    PB_1K=None,
    PB_5K=None,
    PB_10K=None,
    PB_15K=None,
    PB_HALF_MARATHON=None,
    PB_MARATHON=None,
)

_SAMPLE_DATE = date(2025, 1, 1)


def _make_pb(pace_str: str) -> RunningPersonalBest:
    return RunningPersonalBest(achieved_on=_SAMPLE_DATE, pace_str=pace_str)


def _pb_summary(
    *,
    pb_1k: str | None = None,
    pb_5k: str | None = None,
    pb_10k: str | None = None,
    pb_half: str | None = None,
    pb_marathon: str | None = None,
) -> RunningPersonalBestsSummary:
    return RunningPersonalBestsSummary(
        PB_1K=_make_pb(pb_1k) if pb_1k else None,
        PB_5K=_make_pb(pb_5k) if pb_5k else None,
        PB_10K=_make_pb(pb_10k) if pb_10k else None,
        PB_15K=None,
        PB_HALF_MARATHON=_make_pb(pb_half) if pb_half else None,
        PB_MARATHON=_make_pb(pb_marathon) if pb_marathon else None,
    )


class TestParsePaceSecs:
    def test_parses_basic_pace(self) -> None:
        assert _parse_pace_secs('4:30/km') == 270

    def test_parses_pace_with_leading_zero_seconds(self) -> None:
        assert _parse_pace_secs('5:05/km') == 305

    def test_parses_single_digit_minutes(self) -> None:
        assert _parse_pace_secs('3:00/km') == 180


class TestFormatPaceSecs:
    def test_formats_to_string(self) -> None:
        assert _format_pace_secs(270) == '4:30/km'

    def test_pads_seconds(self) -> None:
        assert _format_pace_secs(305) == '5:05/km'

    def test_round_trip(self) -> None:
        assert _format_pace_secs(_parse_pace_secs('6:15/km')) == '6:15/km'


class TestBuildPaceZones:
    def test_no_pbs_returns_none(self) -> None:
        result = build_pace_zones(_NO_PBS)
        assert result is None

    def test_5k_pb_uses_no_adjustment(self) -> None:
        # 5K pace 4:00/km = 240 sec/km, no adjustment → ref=240
        # Easy = 240+65=305 = 5:05/km
        # Marathon = 240+40=280 = 4:40/km
        # Threshold = 240+15=255 = 4:15/km
        # Interval = 240+0=240 = 4:00/km
        result = build_pace_zones(_pb_summary(pb_5k='4:00/km'))
        assert result is not None
        assert result.reference_distance == '5K'
        assert result.easy_pace == '5:05/km'
        assert result.marathon_pace == '4:40/km'
        assert result.threshold_pace == '4:15/km'
        assert result.interval_pace == '4:00/km'

    def test_10k_pb_applies_minus_13_adjustment(self) -> None:
        # 10K pace 4:00/km = 240 sec/km, adjustment=-13 → ref=227
        # Easy = 227+65=292 = 4:52/km
        # Interval = 227+0=227 = 3:47/km
        result = build_pace_zones(_pb_summary(pb_10k='4:00/km'))
        assert result is not None
        assert result.reference_distance == '10K'
        assert result.interval_pace == '3:47/km'
        assert result.easy_pace == '4:52/km'

    def test_5k_takes_priority_over_10k(self) -> None:
        result = build_pace_zones(_pb_summary(pb_5k='4:00/km', pb_10k='3:50/km'))
        assert result is not None
        assert result.reference_distance == '5K'

    def test_half_marathon_pb_applies_minus_30_adjustment(self) -> None:
        # Half pace 4:30/km = 270 sec/km, adjustment=-30 → ref=240
        result = build_pace_zones(_pb_summary(pb_half='4:30/km'))
        assert result is not None
        assert result.reference_distance == 'Half-Marathon'
        assert result.interval_pace == '4:00/km'

    def test_1k_pb_applies_plus_15_adjustment(self) -> None:
        # 1K pace 3:30/km = 210 sec/km, adjustment=+15 → ref=225
        result = build_pace_zones(_pb_summary(pb_1k='3:30/km'))
        assert result is not None
        assert result.reference_distance == '1K'
        assert result.interval_pace == '3:45/km'

    def test_zone_ordering_easy_slowest(self) -> None:
        result = build_pace_zones(_pb_summary(pb_5k='4:00/km'))
        assert result is not None
        easy_secs = _parse_pace_secs(result.easy_pace)
        marathon_secs = _parse_pace_secs(result.marathon_pace)
        threshold_secs = _parse_pace_secs(result.threshold_pace)
        interval_secs = _parse_pace_secs(result.interval_pace)
        assert easy_secs > marathon_secs > threshold_secs >= interval_secs

    def test_all_outputs_are_pace_strings(self) -> None:
        result = build_pace_zones(_pb_summary(pb_5k='4:00/km'))
        assert result is not None
        for pace in (result.easy_pace, result.marathon_pace, result.threshold_pace, result.interval_pace):
            assert '/km' in pace
            assert ':' in pace
