"""Что бот отвечает на сообщения. Здесь нет ничего от Telegram, поэтому логику легко проверить."""
from pathlib import Path

from journal_ai import classify_entry, count_categories, write_summary
from journal_io import append_entry, read_classified

HELP = ('Я веду журнал проделок кота Барсика. Напишите, что он натворил, и я запишу это с категорией. '
        'Команды: /summary - сводка за последние записи, /id - ваш номер в Telegram.')
MAX_LENGTH = 500


def read_allowed(path: Path) -> set[int]:
    """Номера пользователей Telegram, которым можно писать в журнал. Строки с # пропускаем."""
    if not path.is_file():
        return set()
    lines = path.read_text(encoding='utf-8').splitlines()
    return {int(line.strip()) for line in lines if line.strip() and not line.startswith('#')}


def handle_text(model, journal_path: Path, author: str, text: str) -> str:
    text = text.strip()
    if not text:
        return 'Пустую запись в журнал не добавляю.'
    if len(text) > MAX_LENGTH:
        return f'Запись длиннее {MAX_LENGTH} символов. Сократите, пожалуйста.'
    # Разберите запись моделью, добавьте её в журнал и верните ответ для чата.
    raise NotImplementedError('Допишите handle_text в bot_logic.py по подсказкам урока 7')


def summary_reply(model, journal_path: Path, last: int = 10) -> str:
    results = read_classified(journal_path)[-last:]
    if not results:
        return 'В журнале пока нет разобранных записей.'
    return f'Последние записи по категориям: {count_categories(results)}\n\n' + write_summary(model, results)
