import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bot_logic import handle_text, read_allowed
from demo_check import ExampleModel
from journal_io import read_classified


class LessonTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.journal = Path(self.folder.name) / 'journal.xlsx'
        shutil.copy(ROOT / 'data' / 'journal.xlsx', self.journal)

    def tearDown(self):
        self.folder.cleanup()

    def test_entry_saved_with_category(self):
        reply = handle_text(ExampleModel(), self.journal, 'Бабушка', 'Съел мой пирожок')
        self.assertIn('кухня', reply)
        self.assertIn('1', reply)
        last = read_classified(self.journal)[-1]
        self.assertEqual((last['author'], last['text'], last['category'], last['severity']),
                         ('Бабушка', 'Съел мой пирожок', 'кухня', 1))

    def test_too_long_text_not_sent_to_model(self):
        model = ExampleModel()
        handle_text(model, self.journal, 'Папа', 'а' * 600)
        self.assertEqual(model.calls, [])

    def test_allowed_users_from_windows_notepad(self):
        path = Path(self.folder.name) / 'allowed.txt'
        path.write_text('  # семья\n123\n  456  \n', encoding='utf-8-sig')
        self.assertEqual(read_allowed(path), {123, 456})

    def test_allowed_users_file(self):
        path = Path(self.folder.name) / 'allowed.txt'
        path.write_text('# семья\n123\n\n456\n', encoding='utf-8')
        self.assertEqual(read_allowed(path), {123, 456})


if __name__ == '__main__':
    unittest.main()
