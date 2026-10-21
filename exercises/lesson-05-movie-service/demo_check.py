import tempfile
from pathlib import Path

from repository import MovieRepository
from search import SemanticSearch
from service import CatalogService
from web import create_app

ROOT = Path(__file__).resolve().parent
QUERY = 'путешествие во времени'


class ExampleEmbedder:
    """Подставной объект вместо модели эмбеддингов: каждое измерение вектора отвечает за одну тему."""
    TOPICS = [('времен', 'будущ'), ('космос', 'планет'), ('войн', 'истребител'), ('хокке',), ('любов', 'ухаживать')]

    def __init__(self):
        self.calls = []

    def embed(self, text):
        self.calls.append(text)
        lowered = text.casefold()
        return [1.0 + sum(word in lowered for word in words) * 5 for words in self.TOPICS]


def check_exercise():
    model = ExampleEmbedder()
    search = SemanticSearch(model)
    movies = [{'id': 1, 'title': 'Кино про хоккей', 'description': 'Матч с канадцами.'},
              {'id': 2, 'title': 'Машина времени', 'description': 'Герой попадает в будущее.'}]
    found = search.find(QUERY, movies, top=1)
    assert model.calls[0] == SemanticSearch.TASK + QUERY, 'Сначала превратите в вектор запрос с пояснением TASK'
    assert found == [movies[1]], 'Верните список фильмов, самый близкий первым'
    search.find('хоккей', movies)
    assert len(model.calls) == 4, 'Векторы фильмов берите через movie_vector: они считаются один раз'
    # Проверяем весь путь через веб-слой на временной базе, рабочий каталог не трогаем.
    with tempfile.TemporaryDirectory() as folder:
        service = CatalogService(MovieRepository(Path(folder) / 'test.db'), SemanticSearch(ExampleEmbedder()))
        service.load_seed(ROOT / 'data' / 'movies.json')
        client = create_app(service).test_client()
        movie = client.get('/api/search', query_string={'q': QUERY}).get_json()['movies'][0]
    return f'{QUERY} -> {movie["title"]}'


def main():
    try:
        print('Проверка без модели:', check_exercise())
    except NotImplementedError as error:
        print(error)


if __name__ == '__main__':
    main()
