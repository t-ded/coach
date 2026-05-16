from __future__ import annotations

from coach.builders.activity_intensity import build_activity_intensity_profile
from coach.domain.activity import Split
from coach.domain.activity import SportType
from coach.domain.activity_intensity import PaceZone
from coach.domain.personal_bests import RunningPersonalBestsSummary
from coach.tests.utils_for_tests import make_activity

# 5K PB: 20:00 → 4:00/km → v5k = 1000/240 ≈ 4.167 m/s
# 10K PB: 42:00 → 4:12/km → v10k = 1000/252 ≈ 3.968 m/s
_PB_WITH_5K_AND_10K = RunningPersonalBestsSummary(
    PB_1K=None,
    PB_5K=None,
    PB_10K=None,
    PB_15K=None,
    PB_HALF_MARATHON=None,
    PB_MARATHON=None,
)


def _make_pb_summary(
    *,
    pb_5k_seconds: int | None = None,
    pb_10k_seconds: int | None = None,
) -> RunningPersonalBestsSummary:
    from datetime import date

    from coach.domain.personal_bests import RunningPersonalBest

    def pb(distance_meters: float, seconds: int) -> RunningPersonalBest:
        spm = seconds / distance_meters
        km_seconds = spm * 1000
        minutes = int(km_seconds // 60)
        secs = int(km_seconds % 60)
        return RunningPersonalBest(achieved_on=date(2025, 1, 1), pace_str=f'{minutes}:{secs:02d}/km')

    return RunningPersonalBestsSummary(
        PB_1K=None,
        PB_5K=pb(5000, pb_5k_seconds) if pb_5k_seconds else None,
        PB_10K=pb(10000, pb_10k_seconds) if pb_10k_seconds else None,
        PB_15K=None,
        PB_HALF_MARATHON=None,
        PB_MARATHON=None,
    )


def _make_split(speed_ms: float, distance: float = 1000.0, hr: float | None = None) -> Split:
    moving_time = int(distance / speed_ms)
    return Split(
        distance_meters=distance,
        elapsed_time_seconds=moving_time,
        moving_time_seconds=moving_time,
        average_speed_ms=speed_ms,
        average_heartrate=hr,
    )


class TestBuildActivityIntensityProfileReturnsNone:
    def test_returns_none_for_non_run(self) -> None:
        pb_summary = _make_pb_summary(pb_5k_seconds=1200)
        ride = make_activity(sport_type=SportType.RIDE, splits=[_make_split(5.0)])
        assert build_activity_intensity_profile(ride, pb_summary) is None

    def test_returns_none_when_no_splits(self) -> None:
        pb_summary = _make_pb_summary(pb_5k_seconds=1200)
        run = make_activity()
        assert run.splits == []
        assert build_activity_intensity_profile(run, pb_summary) is None

    def test_returns_none_when_no_pbs(self) -> None:
        run = make_activity(splits=[_make_split(3.0)])
        pb_summary = _make_pb_summary()
        assert build_activity_intensity_profile(run, pb_summary) is None


class TestZoneAssignment:
    def setup_method(self) -> None:
        # 5K: 20:00 (1200s) → 4:00/km → v5k = 4.167 m/s
        # 10K: 43:00 (2580s) → 4:18/km → v10k = 3.876 m/s
        self._pb_summary = _make_pb_summary(pb_5k_seconds=1200, pb_10k_seconds=2580)

    def _profile_primary_zone(self, speed_ms: float) -> PaceZone:
        run = make_activity(splits=[_make_split(speed_ms)])
        profile = build_activity_intensity_profile(run, self._pb_summary)
        assert profile is not None
        return profile.primary_zone

    def test_faster_than_5k_pace_is_vo2max(self) -> None:
        # v5k ≈ 4.167, so 4.5 m/s is faster
        assert self._profile_primary_zone(4.5) == PaceZone.Z5_VO2MAX

    def test_near_10k_pace_is_threshold(self) -> None:
        # v10k ≈ 3.876, 92% of that = 3.566; speed of 3.7 should be Z4
        assert self._profile_primary_zone(3.7) == PaceZone.Z4_THRESHOLD

    def test_above_80pct_5k_below_threshold_is_tempo(self) -> None:
        # 80% of v5k = 3.333; just above should be Z3
        assert self._profile_primary_zone(3.4) == PaceZone.Z3_TEMPO

    def test_75_to_80_pct_5k_is_easy(self) -> None:
        # 75-80% of v5k = 3.125-3.333; 3.2 should be Z2
        assert self._profile_primary_zone(3.2) == PaceZone.Z2_EASY

    def test_below_75_pct_5k_is_recovery(self) -> None:
        # < 75% of v5k = < 3.125; 2.5 should be Z1
        assert self._profile_primary_zone(2.5) == PaceZone.Z1_RECOVERY


class TestZoneAssignmentWithOnly5kPb:
    def test_zones_inferred_from_5k_only(self) -> None:
        pb_summary = _make_pb_summary(pb_5k_seconds=1200)
        run = make_activity(splits=[_make_split(3.7)])
        profile = build_activity_intensity_profile(run, pb_summary)
        assert profile is not None
        assert profile.primary_zone == PaceZone.Z4_THRESHOLD


class TestZoneAssignmentWithOnly10kPb:
    def test_zones_inferred_from_10k_only(self) -> None:
        pb_summary = _make_pb_summary(pb_10k_seconds=2580)
        run = make_activity(splits=[_make_split(2.5)])
        profile = build_activity_intensity_profile(run, pb_summary)
        assert profile is not None
        assert profile.primary_zone == PaceZone.Z1_RECOVERY


class TestSplitDetection:
    def setup_method(self) -> None:
        self._pb_summary = _make_pb_summary(pb_5k_seconds=1200)

    def test_negative_split_detected_when_second_half_faster(self) -> None:
        splits = [_make_split(3.0), _make_split(3.0), _make_split(3.5), _make_split(3.5)]
        run = make_activity(splits=splits)
        profile = build_activity_intensity_profile(run, self._pb_summary)
        assert profile is not None
        assert profile.is_negative_split is True

    def test_positive_split_detected_when_second_half_slower(self) -> None:
        splits = [_make_split(3.5), _make_split(3.5), _make_split(3.0), _make_split(3.0)]
        run = make_activity(splits=splits)
        profile = build_activity_intensity_profile(run, self._pb_summary)
        assert profile is not None
        assert profile.is_negative_split is False

    def test_even_split_returns_none(self) -> None:
        splits = [_make_split(3.0), _make_split(3.0), _make_split(3.01), _make_split(3.0)]
        run = make_activity(splits=splits)
        profile = build_activity_intensity_profile(run, self._pb_summary)
        assert profile is not None
        assert profile.is_negative_split is None

    def test_single_split_returns_none(self) -> None:
        run = make_activity(splits=[_make_split(3.0)])
        profile = build_activity_intensity_profile(run, self._pb_summary)
        assert profile is not None
        assert profile.is_negative_split is None


class TestHrDrift:
    def setup_method(self) -> None:
        self._pb_summary = _make_pb_summary(pb_5k_seconds=1200)

    def test_hr_drift_detected_when_second_half_higher(self) -> None:
        splits = [
            _make_split(3.0, hr=140.0),
            _make_split(3.0, hr=142.0),
            _make_split(3.0, hr=155.0),
            _make_split(3.0, hr=157.0),
        ]
        run = make_activity(splits=splits)
        profile = build_activity_intensity_profile(run, self._pb_summary)
        assert profile is not None
        assert profile.hr_drift is not None
        assert profile.hr_drift > 1.05

    def test_no_hr_data_returns_none(self) -> None:
        splits = [_make_split(3.0), _make_split(3.0), _make_split(3.0), _make_split(3.0)]
        run = make_activity(splits=splits)
        profile = build_activity_intensity_profile(run, self._pb_summary)
        assert profile is not None
        assert profile.hr_drift is None

    def test_sparse_hr_coverage_returns_none(self) -> None:
        splits = [
            _make_split(3.0, hr=140.0),
            _make_split(3.0),
            _make_split(3.0),
            _make_split(3.0),
        ]
        run = make_activity(splits=splits)
        profile = build_activity_intensity_profile(run, self._pb_summary)
        assert profile is not None
        assert profile.hr_drift is None


class TestFlags:
    def setup_method(self) -> None:
        self._pb_summary = _make_pb_summary(pb_5k_seconds=1200)

    def test_primary_zone_flag_always_present(self) -> None:
        run = make_activity(splits=[_make_split(3.2)])
        profile = build_activity_intensity_profile(run, self._pb_summary)
        assert profile is not None
        assert any('Z2/Easy' in f for f in profile.flags)

    def test_negative_split_flag_present(self) -> None:
        splits = [_make_split(3.0), _make_split(3.0), _make_split(3.5), _make_split(3.5)]
        run = make_activity(splits=splits)
        profile = build_activity_intensity_profile(run, self._pb_summary)
        assert profile is not None
        assert any('negative split' in f for f in profile.flags)

    def test_positive_split_flag_present(self) -> None:
        splits = [_make_split(3.5), _make_split(3.5), _make_split(3.0), _make_split(3.0)]
        run = make_activity(splits=splits)
        profile = build_activity_intensity_profile(run, self._pb_summary)
        assert profile is not None
        assert any('positive split' in f for f in profile.flags)
