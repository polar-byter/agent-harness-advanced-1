"""Добавляем в ZIP короткие образцы данных и проверяемую арифметику LoRA."""

import argparse
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED


MATRIX_DEMO = '''"""Маленькие матрицы из рисунков урока; модели и библиотеки не нужны."""


def multiply(left, right):
    """Умножить таблицы: строка слева на столбец справа."""
    result = []
    for row in left:
        new_row = []
        for column in range(len(right[0])):
            total = 0
            for index in range(len(row)):
                total += row[index] * right[index][column]
            new_row.append(total)
        result.append(new_row)
    return result


def main():
    base = [[1, 2], [3, 4]]
    matrix_a = [[1, -1]]
    matrix_b = [[2], [1]]
    vector = [[2], [1]]
    # В рисунке alpha / r = 1, поэтому отдельное масштабирование не нужно.
    correction = multiply(matrix_b, matrix_a)
    effective = []
    for row in range(2):
        effective.append([base[row][column] + correction[row][column] for column in range(2)])
    before = multiply(base, vector)
    after = multiply(effective, vector)
    branch = multiply(matrix_b, multiply(matrix_a, vector))
    assert correction == [[2, -2], [1, -1]]
    assert effective == [[3, 0], [4, 3]]
    assert after == [[before[i][0] + branch[i][0]] for i in range(2)]
    if vector == [[2], [1]]:
        assert before == [[4], [10]] and after == [[6], [11]]
        assert branch == [[2], [1]]
    print("Поправка BA:", correction)
    print("Эффективные веса:", effective)
    print("Выход базы:", [row[0] for row in before])
    print("Выход с поправкой:", [row[0] for row in after])


if __name__ == "__main__":
    main()
'''

README = '''# Короткие образцы данных

В train.jsonl, dev.jsonl и exam.jsonl лежат по две записи из основных файлов data.
Они нужны для чтения урока: одинаковая просьба с выбранной книгой и без нее.
В обучающем файле формулировка "Еще на неделю", в разработке "Недели сверху хватит",
в экзамене "Срок увеличьте на неделю". В каждом случае ожидаем renew с книгой и
clarify без нее. Все поля сохранены, в одной строке находится один JSON-объект.

Это сокращенные образцы: категорий find и question в них нет. Команды основного
опыта используют полные файлы data, а не эту папку. Две строки не позволяют
оценить качество классификации.
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    args = parser.parse_args()
    with ZipFile(args.archive) as package:
        assert package.testzip() is None
        files = {name: package.read(name) for name in package.namelist()}
    root = 'fine-tuning-dialogues/'
    for split, group in (('train', 'context-0'), ('dev', 'context-4'), ('exam', 'context-5')):
        records = [json.loads(line) for line in files[root+'data/'+split+'.jsonl'].decode('utf-8').splitlines()]
        selected = [row for row in records if row['template_group'] == group]
        assert len(selected) == 2 and {row['expected'] for row in selected} == {'renew', 'clarify'}
        files[root+'examples/mini-data/'+split+'.jsonl'] = ''.join(
            json.dumps(row, ensure_ascii=False, separators=(',', ':'))+'\n' for row in selected).encode('utf-8')
    files[root+'examples/mini-data/README.md'] = README.encode('utf-8')
    files[root+'examples/matrix_demo.py'] = MATRIX_DEMO.encode('utf-8')
    readme = files[root+'README.md'].decode('utf-8')
    marker = '\n## Наглядные примеры из статьи\n'
    readme = readme.split(marker)[0].rstrip() + '\n' + marker + '''
В examples/mini-data лежат короткие train.jsonl, dev.jsonl и exam.jsonl, по две
строки из полного набора. Они нужны для чтения, основной опыт использует data.

Матрицы с рисунков можно пересчитать без модели:

```powershell
python examples/matrix_demo.py
```

Выход базы будет [4, 10], с придуманной поправкой [6, 11]. Это арифметика
учебного примера, не измерение качества модели и не результат обучения LoRA.
'''
    files[root+'README.md'] = readme.encode('utf-8')
    with ZipFile(args.archive, 'w', compression=ZIP_DEFLATED) as package:
        for name, content in sorted(files.items()):
            info = ZipInfo(name, date_time=(2026, 11, 2, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            package.writestr(info, content)
    print('Архив обновлен:', len(files), 'файлов')


if __name__ == '__main__':
    main()
