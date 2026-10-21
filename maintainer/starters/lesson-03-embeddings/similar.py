"""Поиск похожих обращений по смыслу с помощью эмбеддингов."""
import json
import math
from pathlib import Path


# Qwen3-Embedding точнее, когда перед текстом названа задача сравнения.
TASK = 'Instruct: Найди обращения клиентов о той же проблеме\nQuery: '


def read_requests(path: Path) -> list[dict]:
    """Обращения клиентов: номер и текст."""
    return json.loads(path.read_text(encoding='utf-8'))


def embed_text(model, text: str) -> list[float]:
    """Модель превращает текст в список чисел. Делим на длину, чтобы все векторы были длины 1."""
    vector = model.embed(TASK + text)
    length = math.sqrt(sum(value * value for value in vector))
    return [value / length for value in vector]


def cosine(a: list[float], b: list[float]) -> float:
    """Для векторов длины 1 косинусная близость - это сумма попарных произведений."""
    return sum(x * y for x, y in zip(a, b))


def build_index(model, records: list[dict]) -> list[tuple[dict, list[float]]]:
    """Считаем векторы один раз и храним рядом с обращениями."""
    return [(record, embed_text(model, record['text'])) for record in records]


def find_similar(model, query: str, index: list, top: int = 3) -> list[tuple[float, dict]]:
    if not query.strip():
        raise ValueError('Пустой запрос искать не нужно')
    # Превратите запрос в вектор, оцените близость к каждому обращению и верните лучшие.
    raise NotImplementedError('Допишите find_similar в similar.py по подсказкам урока 3')


def group_duplicates(index: list, threshold: float = 0.7) -> list[list[dict]]:
    """Простая группировка: обращение попадает в группу первого похожего на него."""
    groups = []
    for record, vector in index:
        for group in groups:
            if cosine(vector, group[0][1]) >= threshold:
                group.append((record, vector))
                break
        else:
            groups.append([(record, vector)])
    return [[record for record, _ in group] for group in groups if len(group) > 1]


def find_by_word(records: list[dict], word: str) -> list[dict]:
    """Поиск подстроки из основного курса - для сравнения."""
    word = word.strip().casefold()
    return [record for record in records if word in record['text'].casefold()]
