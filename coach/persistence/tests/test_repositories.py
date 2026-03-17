import pytest

from coach.domain.activity import SportType
from coach.domain.goals import DistanceActivityTrainingGoal
from coach.domain.goals import Priority
from coach.domain.goals import TrainingGoal
from coach.domain.profile import UserProfile
from coach.persistence.sqlite.database import Database
from coach.persistence.sqlite.repositories import SQLiteUserProfileRepository


@pytest.fixture
def repo() -> SQLiteUserProfileRepository:
    return SQLiteUserProfileRepository(Database(':memory:'))


class TestSQLiteUserProfileRepository:
    def test_load_empty(self, repo: SQLiteUserProfileRepository) -> None:
        assert repo.load() is None

    def test_save_and_load_text_only(self, repo: SQLiteUserProfileRepository) -> None:
        profile = UserProfile(
            chat_preferences='Be concise.',
            training_preferences='Lots of intervals.',
            personal_information='Runs 3x/week.',
            constraints='Max 5 days/week.',
        )
        repo.save(profile)
        assert repo.load() == profile

    def test_save_and_load_with_goals(self, repo: SQLiteUserProfileRepository) -> None:
        goals = (
            TrainingGoal(name='Sub-20 5K', sport_type=SportType.RUN, goal_date='N/A', priority=Priority.HIGH),
            DistanceActivityTrainingGoal(
                name='Paris Marathon',
                sport_type=SportType.RUN,
                goal_date='2026-04-15',
                priority=Priority.MEDIUM,
                notes='Target sub-3h',
                goal_distance_meters=42195.0,
                goal_duration_seconds=10800,
                goal_pace='4:16/km',
            ),
        )
        profile = UserProfile(goals=goals)
        repo.save(profile)
        assert repo.load() == profile

    def test_save_overwrites_existing(self, repo: SQLiteUserProfileRepository) -> None:
        repo.save(UserProfile(chat_preferences='First.'))
        updated = UserProfile(chat_preferences='Updated.')
        repo.save(updated)
        assert repo.load() == updated

    def test_delete(self, repo: SQLiteUserProfileRepository) -> None:
        repo.save(UserProfile(chat_preferences='Be concise.'))
        repo.delete()
        assert repo.load() is None

    def test_save_and_load_empty_profile(self, repo: SQLiteUserProfileRepository) -> None:
        repo.save(UserProfile())
        assert repo.load() == UserProfile()
