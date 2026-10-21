from time import perf_counter

from demo_check import DAYS, QUESTION, RULE, check_exercise
from local_llm import ask, load_chat


def main():
    print(QUESTION)
    try:
        # Сначала проверяем упражнение без модели, затем загружаем настоящую.
        check_exercise()
        with load_chat() as model:
            start = perf_counter()
            print('Ответ модели:', ask(model, RULE, QUESTION))
            print('Время ответа, сек:', round(perf_counter() - start, 1))
            data = ask(model, 'Найди в пункте регламента срок возврата в днях.', QUESTION,
                       schema=DAYS, max_tokens=32)
            print('Ответ по схеме:', data, '- тип:', type(data['days']).__name__)
    except (NotImplementedError, FileNotFoundError, ModuleNotFoundError, ValueError) as error:
        print(error)


if __name__ == '__main__':
    main()
