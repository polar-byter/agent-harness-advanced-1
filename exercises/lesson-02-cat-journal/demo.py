from pathlib import Path

from demo_check import check_exercise
from journal_ai import count_categories, process_journal, write_summary
from journal_io import read_journal
from local_llm import load_chat

ROOT = Path(__file__).resolve().parent


def main():
    try:
        check_exercise()
        entries = read_journal(ROOT / 'data' / 'journal.xlsx')
        print('Записей в журнале:', len(entries))
        with load_chat() as model:
            results = process_journal(model, entries)
            for item in results:
                print(f'{item["category"]:>9} | {item["severity"]} | {item["text"]}')
            print('По категориям:', count_categories(results))
            print('Сводка для семьи:', write_summary(model, results))
    except (NotImplementedError, FileNotFoundError, ModuleNotFoundError, ValueError) as error:
        print(error)


if __name__ == '__main__':
    main()
