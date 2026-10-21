from pathlib import Path
from time import perf_counter

from demo_check import check_exercise
from local_llm import load_vision
from photo_check import check_photo, read_returns, route_return

ROOT = Path(__file__).resolve().parent


def main():
    try:
        check_exercise()
        claims = read_returns(ROOT / 'data' / 'returns.json')
        with load_vision() as model:
            for claim in claims:
                start = perf_counter()
                check = check_photo(model, ROOT / 'data' / 'photos' / claim['photo'], claim['item'])
                print(f'{claim["order"]}: {claim["item"]}, причина "{claim["reason"]}", фото {claim["photo"]}')
                print('  Модель:', check)
                print('  Решение:', route_return(check), f'({perf_counter() - start:.0f} сек)')
    except (NotImplementedError, FileNotFoundError, ModuleNotFoundError, ValueError) as error:
        print(error)


if __name__ == '__main__':
    main()
