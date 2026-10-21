from local_llm import ask

RULE = 'Ответь на вопрос клиента по пункту регламента. Если ответа в пункте нет, так и скажи.'
QUESTION = ('Вопрос: Сколько дней есть на возврат товара?\n'
            'Пункт регламента: Возврат товара возможен в течение 14 дней.')
DAYS = {'type': 'object', 'properties': {'days': {'type': 'integer'}}, 'required': ['days']}


class ExampleModel:
    """Подставной объект вместо модели: запоминает вызов и возвращает заданный текст."""

    def __init__(self, content):
        self.content = content
        self.calls = []

    def create_chat_completion(self, **settings):
        self.calls.append(settings)
        return {'choices': [{'finish_reason': 'stop', 'message': {'content': self.content}}]}


def check_exercise():
    model = ExampleModel('<think>\n\n</think>\n\nВернуть товар можно в течение 14 дней.')
    answer = ask(model, RULE, QUESTION)
    assert len(model.calls) == 1, 'Ожидаем одно обращение к модели'
    messages = model.calls[0]['messages']
    assert [item['role'] for item in messages] == ['system', 'user'], 'Нужны два сообщения: system и user'
    assert messages[1]['content'] == QUESTION, 'Во втором сообщении передайте text'
    assert 'response_format' not in model.calls[0], 'Без схемы ограничение JSON не нужно'
    json_model = ExampleModel('{"days": 14}')
    assert ask(json_model, RULE, QUESTION, schema=DAYS) == {'days': 14}, 'Со схемой верните словарь'
    return answer


def main():
    try:
        print('Проверка без модели:', check_exercise())
    except NotImplementedError as error:
        print(error)


if __name__ == '__main__':
    main()
