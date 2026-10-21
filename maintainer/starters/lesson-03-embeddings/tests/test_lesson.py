import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from demo_check import ExampleEmbedder
from similar import build_index, find_similar, read_requests


class LessonTests(unittest.TestCase):
    def setUp(self):
        self.model = ExampleEmbedder()
        self.index = build_index(self.model, read_requests(ROOT / 'data' / 'requests.json'))

    def test_best_match_first(self):
        found = find_similar(self.model, 'деньги списали дважды', self.index, top=2)
        self.assertEqual([record['id'] for _, record in found], ['О-106', 'О-107'])
        self.assertGreaterEqual(found[0][0], found[1][0])

    def test_top_limits_results(self):
        self.assertEqual(len(find_similar(self.model, 'опоздал курьер', self.index, top=1)), 1)
        self.assertEqual(len(find_similar(self.model, 'опоздал курьер', self.index, top=5)), 5)

    def test_empty_query(self):
        with self.assertRaises(ValueError):
            find_similar(self.model, ' ', self.index)


if __name__ == '__main__':
    unittest.main()
