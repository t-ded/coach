from datetime import UTC
from datetime import datetime
import json
from typing import Iterable
from typing import Optional

from coach.domain.models import Activity, ActivitySource, SportType
from coach.persistence.database import Database
from coach.persistence.repository_interface import Repository
from coach.training_state.serialization import deserialize_training_state
from coach.training_state.serialization import serialize_training_state
from coach.training_state.training_state import TrainingState


class SQLiteActivityRepository(Repository[Activity]):
    def __init__(self, db: Database) -> None:
        self._conn = db.connection()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            '''
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
            '''
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
        return '''
            INSERT OR IGNORE INTO activities VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        '''

    @staticmethod
    def _activity_values(
        activity: Activity,
    ) -> tuple[
        int, str, int, str,
        Optional[str], str, int, Optional[int],
        Optional[float], Optional[float], Optional[float], Optional[float], Optional[float],
        int, int,
    ]:
        return (
            activity.activity_id,
            activity.source.value,
            activity.source_activity_id,
            activity.sport_type.value,

            activity.name,
            activity.start_time_utc.isoformat(),
            activity.elapsed_time_seconds,
            activity.moving_time_seconds,

            activity.distance_meters,
            activity.elevation_gain_meters,
            activity.average_heart_rate,
            activity.max_heart_rate,
            activity.average_power_watts,

            int(activity.is_manual),
            int(activity.is_race),
        )

    def list_all(self) -> list[Activity]:
        rows = self._conn.execute('SELECT * FROM activities').fetchall()

        return [
            Activity(
                activity_id=row['activity_id'],
                source=ActivitySource(row['source']),
                source_activity_id=row['source_activity_id'],
                sport_type=SportType(row['sport_type']),
                name=row['name'],
                start_time_utc=row['start_time_utc'],
                elapsed_time_seconds=row['elapsed_time_seconds'],
                moving_time_seconds=row['moving_time_seconds'],
                distance_meters=row['distance_meters'],
                elevation_gain_meters=row['elevation_gain_meters'],
                average_heart_rate=row['average_heart_rate'],
                max_heart_rate=row['max_heart_rate'],
                average_power_watts=row['average_power_watts'],
                is_manual=bool(row['is_manual']),
                is_race=bool(row['is_race']),
            )
            for row in rows
        ]


class SQLiteTrainingStateRepository(Repository[TrainingState]):
    def __init__(self, db: Database) -> None:
        self._conn = db.connection()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS training_state_snapshots
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                persisted_at TEXT NOT NULL,
                training_state_json TEXT NOT NULL
            )
            '''
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
        return '''
            INSERT INTO training_state_snapshots (
                persisted_at, training_state_json
            ) VALUES (
                ?, ?
            )
        '''

    @staticmethod
    def _training_state_values(state: TrainingState) -> tuple[str, str]:
        return (
            datetime.now(tz=UTC).isoformat(),
            json.dumps(serialize_training_state(state)),
        )

    def list_all(self) -> list[TrainingState]:
        rows = self._conn.execute('SELECT * FROM training_state_snapshots ORDER BY generated_at DESC').fetchall()
        return [deserialize_training_state(state) for state in rows]
