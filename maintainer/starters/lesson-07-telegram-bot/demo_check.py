import json
import shutil
import tempfile
from pathlib import Path

from bot_logic import handle_text
from journal_io import read_classified

ROOT = Path(__file__).resolve().parent
TEXT = 'Утащил со стола сосиску'


class ExampleModel:
    """Подставной объект вместо модели: любую запись относит к кухне."""

    def __init__(self):
        self.calls = []

    def create_chat_completion(self, **settings):
        self.calls.append(settings)
        content = json.dumps({'category': 'кухня', 'severity': 1}, ensure_ascii=False)
        return {'choices': [{'finish_reason': 'stop', 'message': {'content': content}}]}


def check_exercise():
    # Работаем с копией журнала, чтобы проверка не меняла data/journal.xlsx.
    with tempfile.TemporaryDirectory() as folder:
        journal = Path(folder) / 'journal.xlsx'
        shutil.copy(ROOT / 'data' / 'journal.xlsx', journal)
        model = ExampleModel()
        reply = handle_text(model, journal, 'Маша', TEXT)
        assert model.calls, 'Передайте запись модели через classify_entry'
        saved = read_classified(journal)
        assert saved and saved[-1]['text'] == TEXT, 'Добавьте запись в журнал вместе с категорией'
        assert saved[-1]['author'] == 'Маша' and saved[-1]['category'] == 'кухня'
    return reply


def main():
    try:
        print('Проверка без модели:', check_exercise())
    except NotImplementedError as error:
        print(error)


if __name__ == '__main__':
    main()
