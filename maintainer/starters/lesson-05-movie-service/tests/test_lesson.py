import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from demo_check import ExampleEmbedder
from repository import MovieRepository
from search import KeywordSearch, SemanticSearch
from service import CatalogService
from web import create_app


class LessonTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.repository = MovieRepository(Path(self.folder.name) / 'test.db')

    def tearDown(self):
        self.folder.cleanup()

    def test_catalog_works_before_exercise(self):
        service = CatalogService(self.repository, KeywordSearch())
        service.load_seed(ROOT / 'data' / 'movies.json')
        app = create_app(service)
        app.testing = True
        client = app.test_client()
        self.assertEqual(client.get('/').status_code, 200)
        self.assertEqual(client.get('/?tag=спорт').status_code, 200)
        self.assertEqual(client.get('/api/search?q=хоккей').get_json(), {'movies': []})
        self.assertEqual(client.post('/movies', data={'title': ''}).status_code, 400)
        response = client.post('/movies', data={
            'title': 'Новый фильм', 'year': '2026', 'description': 'Про хоккей', 'tags': 'спорт'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(client.get('/api/search?q=хоккей').get_json()['movies'][0]['title'], 'Новый фильм')

    def test_semantic_search_in_service(self):
        service = CatalogService(self.repository, SemanticSearch(ExampleEmbedder()))
        service.load_seed(ROOT / 'data' / 'movies.json')
        self.assertEqual(service.find('кино про хоккей', top=1)[0]['title'], 'Легенда номер 17')
        self.assertEqual(len(service.find('космос', top=2)), 2)

    def test_vectors_cached(self):
        model = ExampleEmbedder()
        search = SemanticSearch(model)
        movies = [{'id': 7, 'title': 'А', 'description': 'про войну'}]
        search.find('война', movies)
        search.find('космос', movies)
        self.assertEqual(len(model.calls), 3)

    def test_service_accepts_any_search(self):
        service = CatalogService(self.repository, KeywordSearch())
        service.add_movie('Тест', 2000, 'Фильм про хоккей', ['спорт'])
        self.assertEqual(service.find('хоккей')[0]['title'], 'Тест')


if __name__ == '__main__':
    unittest.main()
