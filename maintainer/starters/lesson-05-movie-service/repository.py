"""Слой хранения: всё, что знает про SQLite, собрано в этом классе."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class MovieRepository:
    def __init__(self, path: Path):
        self.path = path
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS movies (id INTEGER PRIMARY KEY, title TEXT NOT NULL, '
                       'year INTEGER, description TEXT NOT NULL, tags TEXT NOT NULL)')

    @contextmanager
    def connect(self):
        """Соединение на одну операцию: при успехе изменения сохраняются, затем файл закрывается."""
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def add(self, title: str, year: int, description: str, tags: list[str]) -> int:
        with self.connect() as db:
            cursor = db.execute('INSERT INTO movies (title, year, description, tags) VALUES (?, ?, ?, ?)',
                                (title, year, description, json.dumps(tags, ensure_ascii=False)))
            return cursor.lastrowid

    def list_all(self) -> list[dict]:
        with self.connect() as db:
            rows = db.execute('SELECT * FROM movies ORDER BY title').fetchall()
        return [self.to_dict(row) for row in rows]

    def get(self, movie_id: int) -> dict | None:
        with self.connect() as db:
            row = db.execute('SELECT * FROM movies WHERE id = ?', (movie_id,)).fetchone()
        return self.to_dict(row) if row else None

    def count(self) -> int:
        with self.connect() as db:
            return db.execute('SELECT COUNT(*) FROM movies').fetchone()[0]

    @staticmethod
    def to_dict(row) -> dict:
        movie = dict(row)
        movie['tags'] = json.loads(movie['tags'])
        return movie
