import json
from collections.abc import Iterable
from datetime import UTC
from datetime import datetime
from typing import Optional

from coach.domain.models import Activity
from coach.domain.models import TrainingState
from coach.persistence.repository_interface import Repository
from coach.persistence.serialization import deserialize_activity
from coach.persistence.serialization import deserialize_training_state
from coach.persistence.serialization import serialize_activity
from coach.persistence.serialization import serialize_training_state
from coach.persistence.sqlite.database import Database


class SQLiteActivityRepository(Repository[Activity]):
    def __init__(self, db: Database) -> None:
        self._conn = db.connection()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activities (
                activity_id INTEGER PRIMARY KEY,
                source TEXT NOT NULL,
                source_activity_id INTEGER NOT NULL,
                sport_type TEXT NOT NULL,
                name TEXT,
                start_time_utc TEXT NOT NULL,
                elapsed_time_seconds INTEGER NOT NULL,
                moving_time_seconds INTEGER,
                distance_meters REAL,
                elevation_gain_meters REAL,
                average_heart_rate REAL,
                max_heart_rate REAL,
                average_power_watts REAL,
                is_manual INTEGER NOT NULL,
                is_race INTEGER NOT NULL,
                UNIQUE (source, source_activity_id)
            )
            """,
        )
        self._conn.commit()

    def save(self, activity: Activity) -> None:
        self._conn.execute(
            self._insert_activity_query,
            self._activity_values(activity),
        )
        self._conn.commit()

    def save_many(self, activities: Iterable[Activity]) -> None:
        self._conn.executemany(
            self._insert_activity_query,
            [self._activity_values(activity) for activity in activities],
        )
        self._conn.commit()

    @property
    def _insert_activity_query(self) -> str:
        return """
            INSERT OR IGNORE INTO activities VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """

    @staticmethod
    def _activity_values(
        activity: Activity,
    ) -> tuple[
        int, str, int, str,
        Optional[str], str, int, Optional[int],
        Optional[float], Optional[float], Optional[float], Optional[float], Optional[float],
        int, int,
    ]:
        serialized = serialize_activity(activity)

        return (
            serialized['activity_id'],
            serialized['source'],
            serialized['source_activity_id'],
            serialized['sport_type'],

            serialized['name'],
            serialized['start_time_utc'],
            serialized['elapsed_time_seconds'],
            serialized['moving_time_seconds'],

            serialized['distance_meters'],
            serialized['elevation_gain_meters'],
            serialized['average_heart_rate'],
            serialized['max_heart_rate'],
            serialized['average_power_watts'],

            serialized['is_manual'],
            serialized['is_race'],
        )

    def list_all(self) -> list[Activity]:
        rows = self._conn.execute('SELECT * FROM activities').fetchall()
        return [deserialize_activity(row) for row in rows]


class SQLiteTrainingStateRepository(Repository[TrainingState]):
    def __init__(self, db: Database) -> None:
        self._conn = db.connection()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS training_state_snapshots
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                persisted_at TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                window_start TEXT NOT NULL,
                window_end TEXT NOT NULL,
                training_state_json TEXT NOT NULL,
                UNIQUE (window_start, window_end)
            )
            """,
        )
        self._conn.commit()

    def save(self, state: TrainingState) -> None:
        self._conn.execute(
            self._insert_training_state_query,
            self._training_state_values(state),
        )
        self._conn.commit()

    def save_many(self, states: Iterable[TrainingState]) -> None:
        self._conn.executemany(
            self._insert_training_state_query,
            [self._training_state_values(state) for state in states],
        )
        self._conn.commit()

    @property
    def _insert_training_state_query(self) -> str:
        return """
            INSERT OR REPLACE INTO training_state_snapshots (
                persisted_at, generated_at, window_start, window_end, training_state_json
            ) VALUES (
                ?, ?, ?, ?, ?
            )
        """

    @staticmethod
    def _training_state_values(state: TrainingState) -> tuple[str, str, str, str, str]:
        serialized_state = serialize_training_state(state)

        return (
            datetime.now(tz=UTC).isoformat(),
            serialized_state['generated_at'],
            serialized_state['window_start'],
            serialized_state['window_end'],
            json.dumps(serialized_state),
        )

    def list_all(self) -> list[TrainingState]:
        rows = self._conn.execute('SELECT * FROM training_state_snapshots ORDER BY persisted_at DESC').fetchall()
        return [deserialize_training_state(state) for state in rows]
