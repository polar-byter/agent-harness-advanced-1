"""Способы поиска фильмов. У обоих один метод find, поэтому сервис может взять любой."""
import math


def cosine(a: list[float], b: list[float]) -> float:
    """Для векторов длины 1 косинусная близость - это сумма попарных произведений."""
    return sum(x * y for x, y in zip(a, b))


class KeywordSearch:
    """Прежний способ: фильм подходит, если в названии или описании есть слово из запроса."""

    def find(self, query: str, movies: list[dict], top: int = 3) -> list[dict]:
        words = [word for word in query.casefold().split() if len(word) > 3]
        found = [movie for movie in movies
                 if any(word in (movie['title'] + ' ' + movie['description']).casefold() for word in words)]
        return found[:top]


class SemanticSearch:
    """Поиск по смыслу: запрос и фильмы превращаются в векторы, ближайшие векторы - лучшие фильмы."""
    TASK = 'Instruct: Найди фильм по описанию зрителя\nQuery: '

    def __init__(self, model):
        self.model = model
        self.vectors = {}  # номер фильма -> вектор; каждый фильм считаем один раз

    def vector(self, text: str) -> list[float]:
        values = self.model.embed(text)
        length = math.sqrt(sum(value * value for value in values))
        return [value / length for value in values]

    def movie_vector(self, movie: dict) -> list[float]:
        if movie['id'] not in self.vectors:
            self.vectors[movie['id']] = self.vector(movie['title'] + '. ' + movie['description'])
        return self.vectors[movie['id']]

    def find(self, query: str, movies: list[dict], top: int = 3) -> list[dict]:
        # Превратите запрос в вектор, оцените близость к каждому фильму и верните лучшие фильмы.
        raise NotImplementedError('Допишите SemanticSearch.find в search.py по подсказкам урока 5')
