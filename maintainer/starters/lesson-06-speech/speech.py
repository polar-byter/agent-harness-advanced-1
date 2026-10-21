"""Голосовое сообщение клиента: расшифровка Whisper и карточка обращения от языковой модели."""
import wave
from pathlib import Path

from local_llm import ask

SAMPLE_RATE = 16000  # Whisper ждёт 16 000 отсчётов в секунду

CALL_RULE = (
    'По расшифровке голосового сообщения клиента интернет-магазина заполни карточку обращения. '
    'name - имя и фамилия, которыми представился клиент; order - номер заказа; problem - что случилось; '
    'callback - когда перезвонить. Пиши только то, что есть в расшифровке. '
    'Если сведений нет, оставь пустую строку.'
)
CALL_SCHEMA = {
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'order': {'type': 'string'},
        'problem': {'type': 'string'},
        'wish': {'type': 'string', 'enum': ['вернуть деньги', 'обменять товар', 'ремонт', 'консультация', 'другое']},
        'callback': {'type': 'string'},
    },
    'required': ['name', 'order', 'problem', 'wish', 'callback'],
}


def read_wav(path: Path):
    """Читаем WAV 16 кГц, моно, 16 бит и переводим отсчёты в числа от -1 до 1."""
    import numpy
    with wave.open(str(path), 'rb') as sound:
        if (sound.getframerate(), sound.getnchannels(), sound.getsampwidth()) != (SAMPLE_RATE, 1, 2):
            raise ValueError('Нужен WAV: 16 000 Гц, один канал, 16 бит')
        frames = sound.readframes(sound.getnframes())
    return numpy.frombuffer(frames, dtype=numpy.int16).astype(numpy.float32) / 32768


def transcribe(model, audio) -> list[str]:
    # Распознайте речь и соберите строки вида "[00:03] текст".
    raise NotImplementedError('Допишите transcribe в speech.py по подсказкам урока 6')


def call_card(chat_model, lines: list[str]) -> dict:
    return ask(chat_model, CALL_RULE, '\n'.join(lines), schema=CALL_SCHEMA, max_tokens=200)
