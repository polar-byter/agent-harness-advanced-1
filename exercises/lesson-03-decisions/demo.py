import time
from pathlib import Path

from decisions import compare_with_markup, decide, describe, read_json
from demo_check import check_exercise
from local_llm import load_chat

ROOT = Path(__file__).resolve().parent
THRESHOLD = 0.9


def main():
    try:
        check_exercise()
        requests = read_json(ROOT / 'data' / 'requests.json')
        questions = read_json(ROOT / 'data' / 'questions.json')
        with load_chat() as model:
            started = time.perf_counter()
            results = [(request, decide(model, request['text'], questions)) for request in requests]
            seconds = time.perf_counter() - started
        for request, answers in results:
            print(describe(request, answers, THRESHOLD))
        report = compare_with_markup(results, THRESHOLD)
        print(f'Порог {THRESHOLD}. Разложено программой: {report["auto"]}, '
              f'совпало с разметкой: {report["correct"]}. Человеку: {len(report["manual"])}.')
        for number, decision, confidence, expected in report['wrong']:
            print(f'  Расхождение: {number} -> {decision} с уверенностью {confidence:.2f}, по разметке {expected}')
        print(f'В среднем {seconds / len(requests):.1f} с на обращение')
    except (NotImplementedError, FileNotFoundError, ModuleNotFoundError, ValueError) as error:
        print(error)


if __name__ == '__main__':
    main()
