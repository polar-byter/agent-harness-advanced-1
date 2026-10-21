"""Проверка фото из заявки на возврат с помощью модели зрения."""
import base64
import json
from pathlib import Path

from local_llm import clean_answer

PHOTO_RULE = (
    'Ты помогаешь проверять фото товаров по заявкам на возврат. Сначала в item назови предмет на фото. '
    'Затем в same_item ответь, тот же ли это товар, что заказан. Потом скажи, видны ли повреждения: '
    'трещины, сколы, разбитое стекло, вмятины. В comment напиши одно короткое предложение по-русски.'
)
# Поля модель заполняет по порядку: сначала называет предмет, потом сравнивает его с заказом.
PHOTO_SCHEMA = {
    'type': 'object',
    'properties': {
        'item': {'type': 'string', 'maxLength': 60},
        'same_item': {'type': 'boolean'},
        'damage_visible': {'type': 'boolean'},
        'comment': {'type': 'string', 'maxLength': 200},
    },
    'required': ['item', 'same_item', 'damage_visible', 'comment'],
}


def read_returns(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding='utf-8'))


def image_to_data_uri(path: Path) -> str:
    """Картинку передаём внутри сообщения: байты файла записываем текстом base64."""
    if not path.is_file():
        raise FileNotFoundError(f'Нет фото {path}')
    return 'data:image/jpeg;base64,' + base64.b64encode(path.read_bytes()).decode('ascii')


def check_photo(model, photo: Path, ordered_item: str) -> dict:
    # Передайте модели фото и название заказанного товара, ответ получите по схеме PHOTO_SCHEMA.
    raise NotImplementedError('Допишите check_photo в photo_check.py по подсказкам урока 4')


def route_return(check: dict) -> str:
    """Решение о деньгах принимает сотрудник; модель только помогает разложить заявки."""
    if not check['same_item']:
        return 'попросить другое фото: на снимке не заказанный товар'
    if check['damage_visible']:
        return 'сотруднику: на фото видно повреждение'
    return 'сотруднику: на фото повреждений не видно, нужна проверка товара'
