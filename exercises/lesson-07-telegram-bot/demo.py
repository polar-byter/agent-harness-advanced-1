"""Разговор с ботом без Telegram: те же функции, что вызывает bot.py, но сообщения заданы в коде."""
import shutil
from pathlib import Path

from bot_logic import handle_text, summary_reply
from demo_check import check_exercise
from local_llm import load_chat

ROOT = Path(__file__).resolve().parent


def main():
    try:
        check_exercise()
        journal = ROOT / 'data' / 'demo-journal.xlsx'
        shutil.copy(ROOT / 'data' / 'journal.xlsx', journal)
        with load_chat() as model:
            for author, text in [('Маша', 'Утащил со стола сосиску, пока я наливала чай'),
                                 ('Папа', 'Сбросил с полки мои наушники, отломался амбушюр')]:
                print(f'{author}: {text}')
                print('Бот:', handle_text(model, journal, author, text))
            print('Бот на /summary:', summary_reply(model, journal))
    except (NotImplementedError, FileNotFoundError, ModuleNotFoundError, ValueError) as error:
        print(error)


if __name__ == '__main__':
    main()
