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


class LessonTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.repository = MovieRepository(Path(self.folder.name) / 'test.db')

    def tearDown(self):
        self.folder.cleanup()

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
