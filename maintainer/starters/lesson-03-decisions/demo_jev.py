"""Те же обращения и вопросы настоящему Jev через OpenRouter. Тексты уходят в OpenRouter и TypeSafe."""
import urllib.error
from pathlib import Path

from decisions import print_report, read_json
from jev_client import ask_jev

ROOT = Path(__file__).resolve().parent
THRESHOLD = 0.9


def main():
    try:
        requests = read_json(ROOT / 'data' / 'requests.json')
        questions = read_json(ROOT / 'data' / 'questions.json')
        results = [(request, ask_jev(request['text'], questions)) for request in requests]
        print_report(results, THRESHOLD)
    except urllib.error.HTTPError as error:
        print('OpenRouter ответил ошибкой', error.code, error.read().decode('utf-8', 'replace'))
    except (ValueError, OSError) as error:
        print(error)


if __name__ == '__main__':
    main()
