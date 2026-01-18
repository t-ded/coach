from datetime import UTC
from datetime import date
from datetime import datetime

from coach.config.logging import configure_logging
from coach.config.settings import load_strava_settings
from coach.ingestion.strava.client import StravaClient
from coach.ingestion.strava.mapper import StravaMapper
from coach.persistence.sqlite.database import Database
from coach.persistence.sqlite.repositories import SQLiteActivityRepository
from coach.persistence.sqlite.repositories import SQLiteTrainingStateRepository
from coach.builders.training_state import build_training_state

configure_logging()


if __name__ == "__main__":
    load_strava_settings()

    client = StravaClient()
    mapper = StravaMapper()
    db = Database('coach.db')

    activity_repo = SQLiteActivityRepository(db)
    activities = [mapper.map_strava_activity(raw_activity) for raw_activity in client.list_activities()]
    activity_repo.save_many(activities)

    state_repo = SQLiteTrainingStateRepository(db)
    current_state = build_training_state(
        activities=activities,
        window_start=date(2025, 1, 1),
        window_end=date(2026, 1, 1),
        generated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    state_repo.save(current_state)
