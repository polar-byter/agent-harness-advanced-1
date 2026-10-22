from pathlib import Path

from decisions import ask_choice, read_json

ROOT = Path(__file__).resolve().parent
STATE = 'Списали деньги дважды за один заказ'


class ExampleModel:
    """Подставной объект вместо модели: вариант, чьи слова есть в обращении, получает высокую оценку."""
    WORDS = {'Возврат': ('сдать', 'обменять', 'возврат'),
             'Претензия': ('слома', 'разбит', 'не включается', 'не хватает', 'не того'),
             'Доставка': ('курьер', 'доставка', 'привезли', 'где мой заказ'),
             'Оплата': ('списали', 'оплата'), 'Личный': ('кабинет',), 'Да': ('слома', 'разбит')}

    def __init__(self):
        self.prompts = []

    def tokenize(self, text, add_bos=True):
        return [int(text.decode('utf-8'))]  # у каждого номера варианта свой "токен"

    def create_completion(self, prompt, max_tokens, temperature, logits_processor):
        self.prompts.append(prompt)
        state = prompt.split('Обращение клиента: ')[1].split('\n')[0].casefold()
        scores = [0.0] * 10
        for line in prompt.splitlines():
            number, dot, option = line.partition('. ')
            if dot and number.isdigit():
                words = self.WORDS.get(option.split(':')[0].split()[0], ())
                scores[int(number)] = 5.0 * sum(word in state for word in words)
        for processor in logits_processor:
            scores = processor([], scores)
        return {'choices': [{'text': '1'}]}


def check_exercise():
    model = ExampleModel()
    question = read_json(ROOT / 'data' / 'questions.json')['queue']
    answer = ask_choice(model, STATE, question)
    assert isinstance(answer, dict) and answer.get('type') == 'choice', 'Верните словарь с "type": "choice"'
    probabilities = answer.get('probabilities')
    assert isinstance(probabilities, dict) and list(probabilities) == list(question['criteria']), \
        'В probabilities - названия вариантов из criteria в том же порядке'
    assert answer.get('choice') == max(probabilities, key=probabilities.get), 'В choice - самый вероятный вариант'
    assert answer.get('confidence') == probabilities[answer['choice']], 'В confidence - вероятность выбранного варианта'
    return f'{STATE} -> {answer["choice"]}, уверенность {answer["confidence"]:.2f}'


def main():
    try:
        print('Проверка без модели:', check_exercise())
    except NotImplementedError as error:
        print(error)


if __name__ == '__main__':
    main()
