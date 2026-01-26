import sqlite3
from collections.abc import Iterable
from datetime import datetime
from typing import Optional

from coach.domain.activity import Activity
from coach.persistence.repository_interface import Repository
from coach.persistence.serialization import deserialize_activity
from coach.persistence.serialization import serialize_activity
from coach.persistence.sqlite.database import Database
from coach.utils import build_sqlite_where_clause


class SQLiteActivityRepository(Repository[Activity]):
    def __init__(self, db: Database) -> None:
        self._conn = db.connection()
        self._conn.row_factory = sqlite3.Row
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
                description TEXT,
                notes TEXT,
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
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """

    @staticmethod
    def _activity_values(
        activity: Activity,
    ) -> tuple[
        int, str, int,
        str, Optional[str], Optional[str], Optional[str],
        str, int, Optional[int],
        Optional[float], Optional[float],
        Optional[float], Optional[float], Optional[float],
        int, int,
    ]:
        serialized = serialize_activity(activity)

        return (
            serialized['activity_id'],
            serialized['source'],
            serialized['source_activity_id'],

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
            serialized['average_power_watts'],

            serialized['is_manual'],
            serialized['is_race'],
        )

    def list_all(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> list[Activity]:
        base_query = 'SELECT * FROM activities'
        where_query, params = build_sqlite_where_clause(base_query, {'start_time_utc': [('>=', start_date), ('<', end_date)]})
        rows = self._conn.execute(where_query, params).fetchall()
        return [deserialize_activity(row) for row in rows]

    def count(self) -> int:
        return self._conn.execute('SELECT COUNT(*) FROM activities').fetchone()[0]

    def last_activity_timestamp(self) -> Optional[int]:
        row = self._conn.execute('SELECT MAX(start_time_utc) FROM activities').fetchone()
        return int(datetime.fromisoformat(row[0]).timestamp()) if (row and row[0]) else None

    def reset_table(self) -> None:
        self._conn.execute('DROP TABLE IF EXISTS activities')
        self._ensure_schema()
