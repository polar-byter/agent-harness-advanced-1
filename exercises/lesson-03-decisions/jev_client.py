"""Те же вопросы настоящему Jev: HTTP-запрос к API TypeSafe AI.

Нужен ключ API в переменной окружения TYPESAFE_API_KEY. Текст обращения уходит на серверы
TypeSafe, поэтому отправляйте только данные, которые разрешено передавать наружу.
"""
import json
import os
import urllib.request

API_URL = 'https://api.typesafe.ai/v1/systemone'


def ask_jev(state, questions: dict, model: str = 'jev-latest', api_key: str | None = None,
            url: str = API_URL) -> dict:
    """Возвращает словарь answers из ответа Jev: те же ключи, что у decide."""
    key = api_key or os.environ.get('TYPESAFE_API_KEY')
    if not key:
        raise ValueError('Нет ключа API: задайте переменную окружения TYPESAFE_API_KEY')
    body = json.dumps({'state': state, 'model': model, 'questions': questions}, ensure_ascii=False)
    request = urllib.request.Request(url, data=body.encode('utf-8'), method='POST', headers={
        'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode('utf-8'))['answers']
