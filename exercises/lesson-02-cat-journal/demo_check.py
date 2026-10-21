import json
from pathlib import Path

from journal_ai import CATEGORIES, classify_entry, process_journal
from journal_io import read_journal

ROOT = Path(__file__).resolve().parent
TEXT = 'Стащил со стола котлету, пока все смотрели телевизор'


class ExampleModel:
    """Подставной объект вместо модели: по ключевому слову выбирает заранее заданный ответ."""
    ANSWERS = {'котлет': ('кухня', 1), 'штор': ('порча', 2), 'ночи': ('шум', 1)}

    def __init__(self):
        self.calls = []

    def create_chat_completion(self, **settings):
        self.calls.append(settings)
        text = settings['messages'][1]['content']
        category, severity = next((value for key, value in self.ANSWERS.items() if key in text), ('нежности', 1))
        content = json.dumps({'category': category, 'severity': severity}, ensure_ascii=False)
        return {'choices': [{'finish_reason': 'stop', 'message': {'content': content}}]}


def check_exercise():
    model = ExampleModel()
    answer = classify_entry(model, TEXT)
    settings = model.calls[0]
    assert settings['messages'][1]['content'] == TEXT, 'Передайте модели текст записи'
    schema = settings.get('response_format', {}).get('schema', {})
    assert schema['properties']['category']['enum'] == list(CATEGORIES), 'Категории схемы берём из CATEGORIES'
    assert answer == {'category': 'кухня', 'severity': 1}, answer
    results = process_journal(ExampleModel(), read_journal(ROOT / 'data' / 'journal.xlsx'))
    assert len(results) == 12, 'В учебном журнале 12 записей'
    return f'{TEXT} -> {answer["category"]}, серьёзность {answer["severity"]}'


def main():
    try:
        print('Проверка без модели:', check_exercise())
    except NotImplementedError as error:
        print(error)


if __name__ == '__main__':
    main()
