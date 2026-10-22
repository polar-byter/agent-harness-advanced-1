"""Модель отвечает на вопросы об обращении вероятностями, а решение по ним принимает программа.

Вопросы и ответы записаны в формате Jev от TypeSafe AI: типы choice, score и noul.
Отвечает локальная Qwen3: вероятности вариантов берём из её оценок первого токена ответа.
"""
import json
import math
from pathlib import Path

SYSTEM = 'Ты оцениваешь обращения клиентов интернет-магазина. Отвечай только номером варианта.'
# Так шаблон Qwen3 размечает сообщения. Пустой блок <think> в конце просит ответить сразу,
# поэтому первым токеном ответа будет номер варианта.
PROMPT = ('<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n'
          '<|im_start|>assistant\n<think>\n\n</think>\n\n')


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def option_probabilities(model, state: str, instructions: str, options: list[str]) -> list[float]:
    """Вероятность каждого варианта: модель оценивает номера вариантов как первый токен ответа."""
    if not 2 <= len(options) <= 9:
        raise ValueError('Вариантов должно быть от 2 до 9: номер варианта - одна цифра')
    labels = [str(number) for number in range(1, len(options) + 1)]
    lines = '\n'.join(f'{label}. {text}' for label, text in zip(labels, options))
    user = f'Обращение клиента: {state}\n\nВопрос: {instructions}\n{lines}\n\nОтвет (один номер):'
    seen = []

    def remember(tokens, scores):
        seen.append(scores.copy())  # оценки всех токенов словаря перед выбором первого токена
        return scores

    model.create_completion(PROMPT.format(system=SYSTEM, user=user), max_tokens=1, temperature=0,
                            logits_processor=[remember])
    logits = [float(seen[0][model.tokenize(label.encode('utf-8'), add_bos=False)[0]]) for label in labels]
    # Softmax: оценки превращаются в вероятности, которые в сумме дают 1.
    top = max(logits)
    weights = [math.exp(value - top) for value in logits]
    return [weight / sum(weights) for weight in weights]


def ask_choice(model, state: str, question: dict) -> dict:
    """Вопрос choice: какой вариант из criteria подходит. Ответ в том же виде, что у Jev."""
    names = list(question['criteria'])
    values = option_probabilities(model, state, question['instructions'], list(question['criteria'].values()))
    # Соберите вероятности по названиям вариантов, выберите самый вероятный и верните ответ.
    raise NotImplementedError('Допишите ask_choice в decisions.py по подсказкам урока 3')


def ask_score(model, state: str, question: dict) -> dict:
    """Вопрос score: уровень на шкале criteria. score - средний номер уровня с учётом вероятностей."""
    values = option_probabilities(model, state, question['instructions'], question['criteria'])
    return {'type': 'score', 'score': sum(level * value for level, value in enumerate(values)),
            'probabilities': {str(level): value for level, value in enumerate(values)}}


def ask_noul(model, state: str, question: dict) -> dict:
    """Вопрос noul: да или нет. noul - вероятность ответа "да"."""
    # Маленькая модель охотнее выбирает первый вариант, поэтому первым ставим "Нет".
    _, yes = option_probabilities(model, state, question['instructions'], ['Нет', 'Да'])
    return {'type': 'noul', 'noul': yes}


ASK = {'choice': ask_choice, 'score': ask_score, 'noul': ask_noul}


def decide(model, state: str, questions: dict) -> dict:
    """Каждый вопрос задаётся отдельно, как в Jev: ответ на один не влияет на другой."""
    answers = {}
    for name, question in questions.items():
        if question['type'] not in ASK:
            raise ValueError('Неизвестный тип вопроса: ' + question['type'])
        answers[name] = ASK[question['type']](model, state, question)
    return answers


def route(answers: dict, threshold: float = 0.9) -> str:
    """Решение принимает программа: уверенный выбор идёт в очередь, остальное - человеку."""
    queue = answers['queue']
    if queue['choice'] == 'другое' or queue['confidence'] < threshold:
        return 'человеку'
    return queue['choice']


def describe(request: dict, answers: dict, threshold: float = 0.9) -> str:
    """Строка отчёта: решение программы, ответ модели и вопросы да/нет, на которые ответ "да"."""
    queue = answers['queue']
    guess = f'{queue["choice"]} {queue["confidence"]:.2f}'
    marks = ' '.join(name for name, answer in answers.items() if answer['type'] == 'noul' and answer['noul'] >= 0.5)
    return f'{request["id"]} {route(answers, threshold):9} {guess:14} {marks:7} {request["text"]}'


def compare_with_markup(results: list, threshold: float = 0.9) -> dict:
    """Сверяем решения программы с разметкой аналитика в поле queue каждого обращения."""
    report = {'auto': 0, 'correct': 0, 'manual': [], 'wrong': []}
    for request, answers in results:
        decision = route(answers, threshold)
        if decision == 'человеку':
            report['manual'].append(request['id'])
            continue
        report['auto'] += 1
        if decision == request['queue']:
            report['correct'] += 1
        else:
            report['wrong'].append((request['id'], decision, answers['queue']['confidence'], request['queue']))
    return report
