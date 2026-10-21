import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from demo_check import ExampleModel, TEXT
from journal_ai import CATEGORIES, classify_entry


class LessonTests(unittest.TestCase):
    def test_answer_and_schema(self):
        model = ExampleModel()
        self.assertEqual(classify_entry(model, 'Порвал новую штору'), {'category': 'порча', 'severity': 2})
        schema = model.calls[0]['response_format']['schema']
        self.assertEqual(schema['properties']['category']['enum'], list(CATEGORIES))
        self.assertEqual(schema['properties']['severity']['enum'], [1, 2, 3])
        self.assertEqual(sorted(schema['required']), ['category', 'severity'])

    def test_rule_lists_categories(self):
        model = ExampleModel()
        classify_entry(model, TEXT)
        rule = model.calls[0]['messages'][0]['content']
        for name, meaning in CATEGORIES.items():
            self.assertIn(f'{name}: {meaning}', rule)

    def test_empty_text(self):
        with self.assertRaises(ValueError):
            classify_entry(ExampleModel(), '   ')


if __name__ == '__main__':
    unittest.main()
