"""Разбор журнала с помощью локальной модели."""
from collections import Counter

from local_llm import ask

# Короткое объяснение к каждой категории заметно повышает точность маленькой модели.
CATEGORIES = {
    'кухня': 'утащил или пытался утащить еду',
    'порча': 'испортил вещь: порвал, разбил, уронил, испачкал',
    'шум': 'мешал спать, громко орал, будил',
    'нежности': 'ласкался, мурлыкал, спал рядом',
    'охота': 'ловил насекомых, птиц, игрушки, гонялся за чем-то',
}
CLASSIFY_RULE = (
    'Определи категорию проделки кота по записи из семейного журнала. Категории:\n'
    + '\n'.join(f'- {name}: {meaning}' for name, meaning in CATEGORIES.items())
    + '\nСерьёзность: 1 - мелочь, 2 - заметный ущерб, 3 - нужен ремонт или новая покупка.'
)
SUMMARY_RULE = (
    'Ты пишешь шуточную семейную сводку о проделках кота Барсика, как ведущий новостей. '
    'Опирайся только на переданные записи, ничего не добавляй от себя. '
    'Не перечисляй записи по датам: напиши связный текст из трёх-четырёх предложений по-русски.'
)


def classify_entry(model, text: str) -> dict:
    if not text.strip():
        raise ValueError('Пустую запись разбирать не нужно')
    # Опишите допустимый ответ схемой JSON и передайте запись модели.
    raise NotImplementedError('Допишите classify_entry в journal_ai.py по подсказкам урока 2')


def process_journal(model, entries: list[dict], on_progress=None) -> list[dict]:
    """Разбираем записи по одной: так проще понять, на какой из них модель ошиблась."""
    results = []
    for number, entry in enumerate(entries, start=1):
        answer = classify_entry(model, entry['text'])
        results.append({**entry, 'category': answer['category'], 'severity': answer['severity']})
        if on_progress:
            on_progress(number, len(entries))
    return results


def count_categories(results: list[dict]) -> dict:
    return dict(Counter(item['category'] for item in results).most_common())


def write_summary(model, results: list[dict]) -> str:
    counts = count_categories(results)
    # Подлежащее "Барсик" подставляем сами: иначе модель путает, кто натворил, а кто записал.
    lines = [f'- Барсик: {item["text"]} ({item["category"]}; записал(а) {item["author"]})' for item in results]
    data = 'Подсчёт по категориям: ' + str(counts) + '\nЧто натворил кот:\n' + '\n'.join(lines)
    return ask(model, SUMMARY_RULE, data, max_tokens=400)
