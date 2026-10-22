"""Те же обращения и вопросы настоящему Jev. Нужен ключ TYPESAFE_API_KEY, тексты уходят в TypeSafe."""
import urllib.error
from pathlib import Path

from decisions import compare_with_markup, describe, read_json
from jev_client import ask_jev

ROOT = Path(__file__).resolve().parent
THRESHOLD = 0.9


def main():
    try:
        requests = read_json(ROOT / 'data' / 'requests.json')
        questions = read_json(ROOT / 'data' / 'questions.json')
        results = [(request, ask_jev(request['text'], questions)) for request in requests]
        for request, answers in results:
            print(describe(request, answers, THRESHOLD))
        report = compare_with_markup(results, THRESHOLD)
        print(f'Порог {THRESHOLD}. Разложено программой: {report["auto"]}, '
              f'совпало с разметкой: {report["correct"]}. Человеку: {len(report["manual"])}.')
    except urllib.error.HTTPError as error:
        print('Jev ответил ошибкой', error.code, error.read().decode('utf-8', 'replace'))
    except (ValueError, OSError) as error:
        print(error)


if __name__ == '__main__':
    main()
