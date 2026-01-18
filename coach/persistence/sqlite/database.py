import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path: Path | str) -> None:
        self._conn = sqlite3.connect(path)

    def connection(self) -> sqlite3.Connection:
        return self._conn
