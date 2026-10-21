"""Слой правил каталога. Сервис не знает ни про HTTP, ни про SQLite, ни про конкретную модель."""
import json
from pathlib import Path


class CatalogService:
    def __init__(self, repository, search):
        # Зависимости передаются снаружи: так их легко заменить в тестах и при запуске.
        self.repository = repository
        self.search = search

    def add_movie(self, title: str, year: int, description: str, tags: list[str]) -> int:
        title, description = title.strip(), description.strip()
        if not title or not description:
            raise ValueError('Нужны название и описание')
        tags = sorted({tag.strip().casefold() for tag in tags if tag.strip()})
        return self.repository.add(title, year, description, tags)

    def movies(self, tag: str | None = None) -> list[dict]:
        movies = self.repository.list_all()
        return [movie for movie in movies if tag in movie['tags']] if tag else movies

    def find(self, query: str, top: int = 3) -> list[dict]:
        if not query.strip():
            return []
        return self.search.find(query.strip(), self.repository.list_all(), top)

    def all_tags(self) -> list[str]:
        return sorted({tag for movie in self.repository.list_all() for tag in movie['tags']})

    def load_seed(self, path: Path) -> None:
        """Первый запуск: заполняем пустой каталог фильмами из JSON."""
        if self.repository.count():
            return
        for movie in json.loads(path.read_text(encoding='utf-8')):
            self.repository.add(movie['title'], movie['year'], movie['description'], movie['tags'])
