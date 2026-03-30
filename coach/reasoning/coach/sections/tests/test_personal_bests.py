from datetime import UTC
from datetime import datetime
from datetime import timedelta

from coach.domain.personal_bests import RunningPersonalBest
from coach.domain.personal_bests import RunningPersonalBestsSummary
from coach.reasoning.coach.sections.personal_bests import PersonalBestsSection


class TestPersonalBestsSection:
    def test_render(self) -> None:
        today = datetime.now(tz=UTC).date()
        pbs = RunningPersonalBestsSummary(
            PB_1K=RunningPersonalBest(achieved_on=today - timedelta(days=1), pace_str='3:30/km'),
            PB_5K=RunningPersonalBest(achieved_on=today - timedelta(days=365), pace_str='4:00/km'),
            PB_10K=None,
            PB_15K=None,
            PB_HALF_MARATHON=RunningPersonalBest(achieved_on=today - timedelta(days=30), pace_str='4:31/km'),
            PB_MARATHON=None,
        )

        section = PersonalBestsSection(pbs)
        result = section.render()
        expected = f"""----------------------------------------
Running personal bests:
- 1K: 3:30/km on {today - timedelta(days=1)} (1 day ago)
- 5K: 4:00/km on {today - timedelta(days=365)} (365 days ago)
- 10K: No PB recorded
- 15K: No PB recorded
- Half Marathon: 4:31/km on {today - timedelta(days=30)} (30 days ago)
- Marathon: No PB recorded
----------------------------------------"""

        assert result == expected
