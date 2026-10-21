import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from demo_check import ExampleVisionModel
from photo_check import PHOTO_SCHEMA, check_photo


class LessonTests(unittest.TestCase):
    def test_message_and_answer(self):
        model = ExampleVisionModel()
        check = check_photo(model, ROOT / 'data' / 'photos' / 'kettle.jpg', 'электрический чайник')
        self.assertEqual(check['damage_visible'], True)
        settings = model.calls[0]
        self.assertEqual(settings['messages'][0]['role'], 'system')
        image, text = settings['messages'][1]['content']
        self.assertTrue(image['image_url']['url'].startswith('data:image/jpeg;base64,/9j/'))
        self.assertIn('электрический чайник', text['text'])
        self.assertEqual(settings['response_format']['schema'], PHOTO_SCHEMA)

    def test_missing_photo(self):
        with self.assertRaises(FileNotFoundError):
            check_photo(ExampleVisionModel(), ROOT / 'data' / 'photos' / 'нет.jpg', 'чайник')


if __name__ == '__main__':
    unittest.main()
