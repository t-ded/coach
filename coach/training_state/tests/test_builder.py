from datetime import date

from coach.domain.models import Activity
from coach.domain.models import SportType
from coach.tests.utils_for_tests import SAMPLE_RIDE
from coach.tests.utils_for_tests import SAMPLE_RUN
from coach.training_state.builder import build_training_state


class TestBuildTrainingState:
    def test_no_activities(self) -> None:
        state = build_training_state(
            activities=[],
            window_start=date(2024, 1, 1),
            window_end=date(2024, 1, 7),
        )

        assert state.volume_by_sport == {}
        assert state.last_activity_date is None

    def test_activity_outside_window(self) -> None:
        state = build_training_state(
            activities=[SAMPLE_RUN, SAMPLE_RIDE],
            window_start=date(2024, 1, 1),
            window_end=date(2025, 1, 1),
        )

        assert state.last_activity_date == SAMPLE_RUN.start_time_utc.date()
        assert SportType.RIDE not in state.volume_by_sport

    def test_two_activity_types(self) -> None:
        state = build_training_state(
            activities=[SAMPLE_RUN, SAMPLE_RUN, SAMPLE_RIDE],
            window_start=date(2025, 1, 1),
            window_end=date(2025, 1, 7),
        )

        assert state.last_activity_date == SAMPLE_RIDE.start_time_utc.date()

        assert state.volume_by_sport[SportType.RUN].distance_meters == 20_000.0
        assert state.volume_by_sport[SportType.RUN].num_activities == 2
        assert state.volume_by_sport[SportType.RUN].duration_seconds == 7_000

        assert state.volume_by_sport[SportType.RIDE].distance_meters == 20_000.0
        assert state.volume_by_sport[SportType.RIDE].num_activities == 1
        assert state.volume_by_sport[SportType.RIDE].duration_seconds == 3_500
