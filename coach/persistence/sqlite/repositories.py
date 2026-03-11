import json
import sqlite3
from collections.abc import Iterable
from datetime import datetime
from typing import Any
from typing import Optional

from coach.domain.activity import Activity
from coach.domain.goals import TrainingGoal
from coach.domain.profile import UserProfile
from coach.persistence.repository_interface import Repository
from coach.persistence.serialization import _bools_to_ints
from coach.persistence.serialization import deserialize_activity
from coach.persistence.serialization import deserialize_goal
from coach.persistence.serialization import serialize_activity
from coach.persistence.serialization import serialize_goal
from coach.persistence.sqlite.database import Database
from coach.utils import build_sqlite_where_clause


class SQLiteUserProfileRepository:
    def __init__(self, db: Database) -> None:
        self._conn = db.connection()
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    _LOCAL_USER_ID = 'local'

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                user_id TEXT NOT NULL PRIMARY KEY,
                chat_preferences TEXT,
                training_preferences TEXT,
                personal_information TEXT,
                constraints TEXT,
                goals TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        self._conn.commit()

    def load(self) -> Optional[UserProfile]:
        row = self._conn.execute('SELECT * FROM profiles WHERE user_id = ?', (self._LOCAL_USER_ID,)).fetchone()
        return self._from_row(dict(row)) if row else None

    def save(self, profile: UserProfile) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO profiles
                (user_id, chat_preferences, training_preferences, personal_information, constraints, goals, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            self._to_row(profile),
        )
        self._conn.commit()

    @staticmethod
    def _from_row(row: dict) -> UserProfile:
        goals: Optional[tuple[TrainingGoal, ...]] = None
        if row['goals'] is not None:
            goals = tuple(deserialize_goal(g) for g in json.loads(row['goals']))
        return UserProfile(
            chat_preferences=row['chat_preferences'],
            training_preferences=row['training_preferences'],
            personal_information=row['personal_information'],
            constraints=row['constraints'],
            goals=goals,
        )

    def _to_row(self, profile: UserProfile) -> tuple[str, Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        goals_json = json.dumps([serialize_goal(g) for g in profile.goals]) if profile.goals is not None else None
        return self._LOCAL_USER_ID, profile.chat_preferences, profile.training_preferences, profile.personal_information, profile.constraints, goals_json

    def delete(self) -> None:
        self._conn.execute('DELETE FROM profiles WHERE user_id = ?', (self._LOCAL_USER_ID,))
        self._conn.commit()


class SQLiteActivityRepository(Repository[Activity]):
    def __init__(self, db: Database) -> None:
        self._conn = db.connection()
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY,
                sport_type TEXT NOT NULL,
                name TEXT,
                description TEXT,
                notes TEXT,
                start_time_utc TEXT NOT NULL,
                elapsed_time_seconds INTEGER NOT NULL,
                moving_time_seconds INTEGER,
                distance_meters REAL,
                elevation_gain_meters REAL,
                average_heart_rate REAL,
                max_heart_rate REAL,
                is_manual INTEGER NOT NULL,
                is_race INTEGER NOT NULL,
                pbs TEXT DEFAULT '[]',
                UNIQUE (id)
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

    def _activity_values(self, activity: Activity) -> tuple[
        int,
        str, Optional[str], Optional[str], Optional[str],
        str, int, Optional[int],
        Optional[float], Optional[float],
        Optional[float], Optional[float],
        int, int, str,
    ]:
        serialized = self._to_row(activity)

        return (
            serialized['id'],

            serialized['sport_type'],
            serialized['name'],
            serialized['description'],
            serialized['notes'],

            serialized['start_time_utc'],
            serialized['elapsed_time_seconds'],
            serialized['moving_time_seconds'],

            serialized['distance_meters'],
            serialized['elevation_gain_meters'],

            serialized['average_heart_rate'],
            serialized['max_heart_rate'],

            serialized['is_manual'],
            serialized['is_race'],

            serialized['pbs'],
        )

    def list_all(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> list[Activity]:
        base_query = 'SELECT * FROM activities'
        where_query, params = build_sqlite_where_clause(base_query, {'start_time_utc': [('>=', start_date), ('<', end_date)]})
        rows = self._conn.execute(where_query, params).fetchall()
        return [self._from_row(row) for row in rows]

    def count(self) -> int:
        return self._conn.execute('SELECT COUNT(*) FROM activities').fetchone()[0]

    def last_activity_timestamp(self) -> Optional[int]:
        row = self._conn.execute('SELECT MAX(start_time_utc) FROM activities').fetchone()
        return int(datetime.fromisoformat(row[0]).timestamp()) if (row and row[0]) else None

    def reset_table(self) -> None:
        self._conn.execute('DROP TABLE IF EXISTS activities')
        self._ensure_schema()

    @staticmethod
    def _to_row(activity: Activity) -> dict[str, Any]:
        row = serialize_activity(activity)
        row = _bools_to_ints(row)
        row['pbs'] = json.dumps(row['pbs'])
        return row

    @staticmethod
    def _from_row(row: dict[str, Any]) -> Activity:
        normalized = dict(row)
        normalized['pbs'] = json.loads(normalized['pbs'])
        return deserialize_activity(normalized)
