from __future__ import annotations

from datetime import UTC
from datetime import datetime

from coach.domain.activity_intensity import ActivityIntensityProfile
from coach.domain.activity_intensity import PaceZone
from coach.domain.activity_intensity import ZoneDistribution
from coach.reasoning.coach.sections.activity_intensity import ActivityIntensitySection


def _make_profile(
    *,
    activity_id: int = 1,
    zones: list[ZoneDistribution] | None = None,
    primary_zone: PaceZone = PaceZone.Z2_EASY,
    is_negative_split: bool | None = None,
    hr_drift: float | None = None,
    flags: list[str] | None = None,
) -> ActivityIntensityProfile:
    if zones is None:
        zones = [ZoneDistribution(zone=PaceZone.Z2_EASY, distance_meters=8000.0, time_seconds=2880)]
    if flags is None:
        flags = ['Z2/Easy easy run (100%)']
    return ActivityIntensityProfile(
        activity_id=activity_id,
        zone_distribution=zones,
        primary_zone=primary_zone,
        is_negative_split=is_negative_split,
        hr_drift=hr_drift,
        flags=flags,
    )


class TestActivityIntensitySectionRendersNone:
    def test_renders_none_when_no_profiles(self) -> None:
        section = ActivityIntensitySection([])
        assert section.render() is None


class TestActivityIntensitySectionRendersProfiles:
    def setup_method(self) -> None:
        start_time = datetime(2025, 5, 12, 7, 0, 0, tzinfo=UTC)
        profile = _make_profile()
        self._section = ActivityIntensitySection([(start_time, 'Morning Run', profile)])
        self._result = self._section.render()

    def test_render_is_not_none(self) -> None:
        assert self._result is not None

    def test_activity_name_in_output(self) -> None:
        assert 'Morning Run' in self._result  # type: ignore[operator]

    def test_zone_percentage_in_output(self) -> None:
        assert 'Z2/Easy' in self._result  # type: ignore[operator]
        assert '100%' in self._result  # type: ignore[operator]

    def test_date_formatted_correctly(self) -> None:
        assert 'Mon 12 May' in self._result  # type: ignore[operator]


class TestActivityIntensitySectionWithFlags:
    def test_split_flag_appears_after_pipe(self) -> None:
        profile = _make_profile(
            is_negative_split=False,
            flags=['Z2/Easy easy run (80%)', 'positive split — faded in second half'],
        )
        section = ActivityIntensitySection([(datetime(2025, 5, 12, tzinfo=UTC), 'Easy Run', profile)])
        result = section.render()
        assert result is not None
        assert 'positive split' in result

    def test_no_extra_pipe_when_only_primary_flag(self) -> None:
        profile = _make_profile(flags=['Z2/Easy easy run (100%)'])
        section = ActivityIntensitySection([(datetime(2025, 5, 12, tzinfo=UTC), 'Easy Run', profile)])
        result = section.render()
        assert result is not None
        assert '|' not in result

    def test_multiple_activities_all_appear(self) -> None:
        p1 = _make_profile(activity_id=1)
        p2 = _make_profile(activity_id=2)
        profiles = [
            (datetime(2025, 5, 12, tzinfo=UTC), 'Run A', p1),
            (datetime(2025, 5, 14, tzinfo=UTC), 'Run B', p2),
        ]
        section = ActivityIntensitySection(profiles)
        result = section.render()
        assert result is not None
        assert 'Run A' in result
        assert 'Run B' in result

    def test_header_is_correct(self) -> None:
        section = ActivityIntensitySection([])
        assert section.header == 'Activity intensity breakdown:'
