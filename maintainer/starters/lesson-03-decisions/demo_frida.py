"""Те же обращения и вопросы открытой модели FRIDA-Decisions на вашем процессоре."""
import time
from pathlib import Path

from decisions import print_report, read_json
from frida_client import ask_frida, load_frida

ROOT = Path(__file__).resolve().parent
# Уверенность FRIDA считается иначе, чем в ask_choice, поэтому порог для неё подбирают заново.
THRESHOLD = 0.9


def main():
    try:
        requests = read_json(ROOT / 'data' / 'requests.json')
        questions = read_json(ROOT / 'data' / 'questions.json')
        judge = load_frida()
        started = time.perf_counter()
        results = [(request, ask_frida(judge, request['text'], questions)) for request in requests]
        seconds = time.perf_counter() - started
        print_report(results, THRESHOLD)
        print(f'В среднем {seconds / len(requests):.1f} с на обращение')
    except ModuleNotFoundError:
        print('Не установлена библиотека frida-decisions: команда установки - в начале frida_client.py')
    except (ValueError, OSError) as error:
        print(error)


if __name__ == '__main__':
    main()
