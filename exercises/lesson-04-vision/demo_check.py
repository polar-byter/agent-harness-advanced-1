import json
from pathlib import Path

from photo_check import check_photo, route_return

ROOT = Path(__file__).resolve().parent
PHOTO = ROOT / 'data' / 'photos' / 'phone.jpg'


class ExampleVisionModel:
    """Подставной объект вместо модели зрения: возвращает заранее заданный ответ."""

    def __init__(self):
        self.calls = []

    def create_chat_completion(self, **settings):
        self.calls.append(settings)
        content = json.dumps({'item': 'смартфон', 'same_item': True, 'damage_visible': True,
                              'comment': 'Задняя панель смартфона разбита.'}, ensure_ascii=False)
        return {'choices': [{'finish_reason': 'stop', 'message': {'content': content}}]}


def check_exercise():
    model = ExampleVisionModel()
    check = check_photo(model, PHOTO, 'смартфон')
    parts = model.calls[0]['messages'][1]['content']
    assert parts[0]['type'] == 'image_url', 'Первая часть сообщения - картинка'
    assert parts[0]['image_url']['url'].startswith('data:image/jpeg;base64,'), 'Передайте фото через image_to_data_uri'
    assert parts[1]['text'].endswith('смартфон'), 'Во второй части назовите заказанный товар'
    assert 'schema' in model.calls[0]['response_format'], 'Ответ ограничиваем схемой PHOTO_SCHEMA'
    return route_return(check)


def main():
    try:
        print('Проверка без модели:', check_exercise())
    except NotImplementedError as error:
        print(error)


if __name__ == '__main__':
    main()
