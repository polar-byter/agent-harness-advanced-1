"""Общий формат учебного набора для библиотечных обращений."""

import json
from pathlib import Path


CATEGORIES = ("renew", "find", "question", "clarify")
MODEL_NAME = "Qwen/Qwen3-0.6B"
SYSTEM_MESSAGE = (
    "Выбери категорию обращения читателя библиотеки с учетом контекста. "
    "renew означает прямую просьбу продлить известную выдачу книги. "
    "find означает просьбу найти книгу в каталоге. "
    "question означает вопрос о правилах или отказ от изменения. "
    "clarify означает что для понимания просьбы не хватает предмета разговора. "
    'Верни только JSON вида {"category":"renew"}. Ничего не выполняй.'
)


def load_records(path: Path) -> list[dict]:
    """Прочитать и проверить учебные строки без библиотек машинного обучения."""
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not records:
        raise ValueError("Набор пуст")
    for record in records:
        if record["expected"] not in CATEGORIES:
            raise ValueError("Неизвестная категория")
        if not isinstance(record["utterance"], str) or not record["utterance"].strip():
            raise ValueError("Нужна непустая реплика")
        if not isinstance(record["context"], dict):
            raise ValueError("Контекст должен быть объектом")
    return records


def make_messages(record: dict) -> list[dict]:
    """Отделить инструкцию модели от данных учебного обращения."""
    return [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": json.dumps(
            {"utterance": record["utterance"], "context": record["context"]}, ensure_ascii=False)},
    ]


def make_target(record: dict) -> str:
    return json.dumps({"category": record["expected"]}, ensure_ascii=False)


def make_training_tokens(tokenizer, record: dict, max_tokens: int = 1024) -> tuple[list[int], list[int]]:
    """Учить только ответу не обрезая длинный пример молча."""
    prompt = tokenizer.apply_chat_template(make_messages(record), tokenize=False,
                                          add_generation_prompt=True, enable_thinking=False)
    prefix = tokenizer.encode(prompt, add_special_tokens=False)
    target = tokenizer.encode(make_target(record) + tokenizer.eos_token, add_special_tokens=False)
    input_tokens = prefix + target
    if not prefix or not target or len(input_tokens) > max_tokens:
        raise ValueError("Пустая последовательность или превышен предел длины")
    labels = [-100] * len(prefix) + target
    return input_tokens, labels
