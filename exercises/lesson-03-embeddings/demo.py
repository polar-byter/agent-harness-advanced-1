from pathlib import Path

from demo_check import QUERY, check_exercise
from local_llm import load_embedder
from similar import build_index, find_by_word, find_similar, group_duplicates, read_requests

ROOT = Path(__file__).resolve().parent


def main():
    try:
        check_exercise()
        records = read_requests(ROOT / 'data' / 'requests.json')
        print('Запрос:', QUERY)
        print('Поиск по слову "сломан":', [record['id'] for record in find_by_word(records, 'сломан')])
        with load_embedder() as model:
            index = build_index(model, records)
            print('Длина вектора:', len(index[0][1]))
            for score, record in find_similar(model, QUERY, index):
                print(f'{score:.3f} {record["id"]} {record["text"]}')
            print('Группы похожих обращений:')
            for group in group_duplicates(index):
                print(' ', ' | '.join(record['text'] for record in group))
    except (NotImplementedError, FileNotFoundError, ModuleNotFoundError, ValueError) as error:
        print(error)


if __name__ == '__main__':
    main()
