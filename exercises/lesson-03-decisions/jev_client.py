"""Те же вопросы настоящему Jev через OpenRouter.

Ключ берётся из переменной окружения OPENROUTER_API_KEY, а если её нет - из подключения основного
курса, которое сохраняет configure_model.py с сервисом OpenRouter. Текст обращения уходит в OpenRouter
и TypeSafe, поэтому отправляйте только данные, которые разрешено передавать наружу.
"""
import json
import os
import urllib.request
from pathlib import Path

API_URL = 'https://openrouter.ai/api/alpha/decisions'
MODEL = 'typesafe/jev-1.14'


def connection_path() -> Path:
    """Тот же файл подключения, что в основном курсе."""
    override = os.environ.get('HARNESS_CONNECTION_FILE')
    if override:
        return Path(override)
    folder = Path(os.environ.get('LOCALAPPDATA', Path.home() / '.config'))
    return folder / 'AgentHarnessWorkshop' / 'connection.json'


def openrouter_key() -> str:
    key = os.environ.get('OPENROUTER_API_KEY')
    if key:
        return key
    path = connection_path()
    if path.is_file():
        settings = json.loads(path.read_text(encoding='utf-8'))
        if settings.get('provider') == 'openrouter' and settings.get('api_key'):
            return settings['api_key']
    raise ValueError('Нет ключа OpenRouter: настройте подключение configure_model.py из основного курса '
                     'или задайте переменную окружения OPENROUTER_API_KEY')


def ask_jev(state, questions: dict, model: str = MODEL, api_key: str | None = None,
            url: str = API_URL) -> dict:
    """Возвращает словарь answers из ответа Jev: те же ключи, что у decide."""
    key = openrouter_key() if api_key is None else api_key
    if not key:
        raise ValueError('Пустой ключ OpenRouter')
    body = json.dumps({'model': model, 'state': state, 'questions': questions}, ensure_ascii=False)
    request = urllib.request.Request(url, data=body.encode('utf-8'), method='POST', headers={
        'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode('utf-8'))['answers']
