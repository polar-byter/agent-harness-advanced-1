"""Создать небольшой синтетический набор без чтения личных разговоров."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


SCENARIOS = {
    "renew": [
        "Продлите выдачу книги {book} на неделю",
        "Я еще читаю {book}, увеличьте срок выдачи",
        "Оставьте мне {book} еще на семь дней",
        "Хочу подольше подержать {book}, продлите выдачу",
        "Поменяйте срок возврата книги {book} на неделю позже",
        "Разрешите еще неделю читать {book}, оформите продление",
    ],
    "find": [
        "Найдите в каталоге книгу {book}",
        "Покажите карточку книги {book}",
        "Поищите {book} в библиотеке",
        "Нужен поиск издания {book}",
        "Отыщите для меня книгу {book}",
        "Посмотрите по каталогу, где есть {book}",
    ],
    "question": [
        "Можно ли вообще продлевать книги, например {book}",
        "Как работает продление книги {book}, ничего пока не оформляйте",
        "Сколько раз разрешено продлевать {book}",
        "Я пока спрашиваю о правилах возврата {book}, без изменений",
        "Не продлевайте {book}, сначала объясните правила",
        "Вы умеете продлевать {book} или надо идти к библиотекарю",
    ],
    "clarify": [
        "Продлите это на неделю",
        "Хочу оставить ее подольше",
        "Пусть срок станет больше",
        "Сделайте для нее продление",
        "Ту самую оставьте еще на неделю",
        "Дайте подольше почитать",
    ],
}


def build_records() -> list[dict]:
    records = []
    for category, templates in SCENARIOS.items():
        for index, template in enumerate(templates):
            split = "train" if index < 4 else "dev" if index == 4 else "exam"
            books = ("Маяк на острове", "Атлас старых дорог") if category != "clarify" else ("",)
            for book_number, book in enumerate(books):
                records.append({
                    "id": f"{category}-{index}-{book_number}",
                    "template_group": f"{category}-{index}", "split": split,
                    "utterance": template.format(book=book),
                    "context": {"current_loan": book} if category == "renew" else {},
                    "expected": category,
                })
    # Одинаковые слова при разном состоянии требуют разных ответов
    for index, phrase in enumerate(("Еще на неделю", "Добавьте семь дней", "Пусть будет на неделю дольше",
                                   "Хочу еще неделю", "Недели сверху хватит", "Срок увеличьте на неделю")):
        split = "train" if index < 4 else "dev" if index == 4 else "exam"
        for has_loan in (False, True):
            records.append({
                "id": f"context-{index}-{int(has_loan)}", "template_group": f"context-{index}",
                "split": split, "utterance": phrase,
                "context": {"current_loan": "Письма с орбиты"} if has_loan else {},
                "expected": "renew" if has_loan else "clarify",
            })
    return records


def validate_records(records: list[dict]) -> None:
    groups = {}
    examples = set()
    for record in records:
        group = record["template_group"]
        if groups.setdefault(group, record["split"]) != record["split"]:
            raise ValueError("Один шаблон оказался в разных частях набора")
        signature = json.dumps([record["utterance"], record["context"]], ensure_ascii=False, sort_keys=True)
        if signature in examples:
            raise ValueError("Повторяется входной пример")
        examples.add(signature)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data"))
    args = parser.parse_args()
    records = build_records()
    validate_records(records)
    args.output.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for split in ("train", "dev", "exam"):
        selected = [record for record in records if record["split"] == split]
        path = args.output / f"{split}.jsonl"
        path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in selected), encoding="utf-8", newline="\n")
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {"source": "Заново придуманные библиотечные ситуации для учебного дополнения",
                "counts": dict(Counter(record["split"] for record in records)), "sha256": hashes,
                "limitation": "Малый шаблонный набор показывает процедуру, но не доказывает качество для живых пользователей"}
    (args.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(manifest["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
