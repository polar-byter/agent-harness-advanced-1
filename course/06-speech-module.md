# Дополнительно: Как устроен speech.py

> **Для кого этот материал:** В Уроке 6 мы объединили речевую модель Whisper и языковую модель Qwen3 в конвейер обработки звонков.
> 
> Здесь мы подробно разберем модуль `speech.py`: нормализацию звуковых отсчетов, работу с сегментами и заполнение структурированной карточки.

---

## 1. Чтение и нормализация звука: read_wav

```python
import wave
from pathlib import Path

def read_wav(path: Path) -> list[float]:
    with wave.open(str(path), 'rb') as wav:
        if wav.getnchannels() != 1 or wav.getframerate() != 16000 or wav.getsampwidth() != 2:
            raise ValueError('Нужен WAV: 16 000 Гц, один канал, 16 бит')
        frames = wav.readframes(wav.getnframes())
        samples = [int.from_bytes(frames[i:i+2], 'little', signed=True) / 32768.0 
                   for i in range(0, len(frames), 2)]
        return samples
```
1. `wave.open(...)`: стандартный модуль Python для чтения аудиоформата WAV.
2. Проверка контракта:
   * `getnchannels() == 1`: моно (один звуковой канал).
   * `getframerate() == 16000`: ровно 16 кГц (стандарт для Whisper).
   * `getsampwidth() == 2`: 16 бит на отсчет (2 байта).
3. `int.from_bytes(..., signed=True) / 32768.0`: превращает двухбайтовые целые числа со знаком в диапазон нормализованных чисел с плавающей точкой от `-1.0` до `+1.0`.

---

## 2. Функция transcribe: Сегменты и временные метки

```python
def transcribe(model, audio: list[float]) -> list[str]:
    segments = model.transcribe(audio, language='ru')
    lines = []
    for segment in segments:
        seconds = segment.t0 // 100
        lines.append(f'[{seconds // 60:02}:{seconds % 60:02}] {segment.text.strip()}')
    return lines
```
* `language='ru'`: указывает модели русский язык, предотвращая нежелательный автоперевод на английский.
* `segment.t0`: отметка начала реплики в сотых долях секунды.
* `f'[{seconds // 60:02}:{seconds % 60:02}]'`: превращает секунды в привычный формат минут и секунд `[00:07]`.

---

## 3. Сборка карточки звонка: call_card

```python
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

def call_card(model, transcript_lines: list[str]) -> dict:
    text = '
'.join(transcript_lines)
    return ask(model, CALL_RULE, text, schema=CALL_SCHEMA, max_tokens=256)
```
* Схема JSON гарантирует: поле `wish` (пожелание клиента) примет ровно одно из допустимых бизнес-значений.
* Карточка автоматически извлекает ключевые факты, сохраняя связь с исходной стенограммой звонка.

---

Вернуться к:
* [Уроку 6. Расшифровка голосового сообщения](06-speech.md)
* [Оглавлению второй ступени](README.md)
