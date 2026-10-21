import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from demo_check import ExampleWhisper
from speech import transcribe


class LessonTests(unittest.TestCase):
    def test_time_marks(self):
        self.assertEqual(transcribe(ExampleWhisper(), []), [
            '[00:00] Здравствуйте.', '[00:07] Две недели назад я купила у вас электрический чайник,'])

    def test_minutes(self):
        model = ExampleWhisper()
        model.transcribe = lambda audio, **settings: [SimpleNamespace(t0=12550, t1=12800, text='  Спасибо. ')]
        self.assertEqual(transcribe(model, []), ['[02:05] Спасибо.'])


if __name__ == '__main__':
    unittest.main()
