"""Собираем каркасы уроков из maintainer/starters и упаковываем их в ZIP рядом с уроками Obsidian.

Каркас = исходные файлы урока + общий local_llm.py + get_models.py, requirements.txt,
.gitignore и TASK.md, который собирается из текста урока в Obsidian.
"""
import argparse
import json
import re
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
STARTERS = ROOT / 'maintainer' / 'starters'
SOLUTIONS = ROOT / 'maintainer' / 'solutions'
RUNTIME = ROOT / 'tools' / 'model_runtime' / 'local_llm.py'
STUB = re.compile(r'^( +)# [^\n]*\n\1raise NotImplementedError\([^\n]*\)\n', re.M)
TASK_SECTIONS = ('Напишите сами', 'Подключите', 'Угадайте', 'Запуст', 'Попробуйте сломать')
GITIGNORE = '.venv/\n.idea/\n__pycache__/\n*.db\ndata/demo-journal.xlsx\n'

GET_MODELS = '''"""Скачивает модели этого урока в общую папку моделей курса."""
import sys

from local_llm import download, models_dir

MODELS = {models}


def main():
    print('Папка моделей:', models_dir())
    # Run с параметром small скачает маленькую языковую модель вместо основной.
    small = 'small' in sys.argv[1:]
    download(*[('chat-small' if small and name == 'chat' else name) for name in MODELS])


if __name__ == '__main__':
    main()
'''


def load_config() -> dict:
    return json.loads((ROOT / 'tools' / 'course-map.json').read_text(encoding='utf-8'))


def apply_solution(text: str, block: str) -> str:
    """Заменяем первую заглушку (комментарий + raise NotImplementedError) эталонным кодом."""
    replaced, count = STUB.subn(block if block.endswith('\n') else block + '\n', text, count=1)
    assert count == 1, 'Заглушка не найдена'
    return replaced


def solved_file(root: str, relative: str, text: str) -> str:
    """Эталонное решение: блок .txt заменяет заглушку, файл без .txt заменяет исходник целиком."""
    whole = SOLUTIONS / root / relative
    if whole.is_file():
        return whole.read_text(encoding='utf-8')
    block = SOLUTIONS / root / (relative + '.txt')
    return apply_solution(text, block.read_text(encoding='utf-8')) if block.is_file() else text


def plain_text(markdown: str) -> str:
    markdown = re.sub(r'!\[\[[^\]]+\]\]\n?', '', markdown)
    markdown = re.sub(r'\[\[[^\]|]+\|([^\]]+)\]\]', r'\1', markdown)
    markdown = re.sub(r'\[\[([^\]|#]+)(?:#[^\]]*)?\]\]', lambda m: Path(m.group(1)).stem, markdown)
    # Раскрывающиеся примечания Obsidian превращаем в обычный текст с подзаголовком.
    def callout(match):
        body = re.sub(r'^> ?', '', match.group(2), flags=re.M).strip()
        return f'**{match.group(1).strip()}**\n\n{body}\n'
    return re.sub(r'^> \[!\w+\]-?\s*(.*?)\n((?:>.*(?:\n|$))+)', callout, markdown, flags=re.M)


def task_text(lesson: dict, note: Path) -> str:
    """TASK.md: "Где мы" и практические разделы урока, без длинных объяснений."""
    text = re.sub(r'\A---\n.*?\n---\n', '', note.read_text(encoding='utf-8'), count=1, flags=re.S)
    where = re.search(r'^> \*\*Где мы\.\*\*.*?(?=\n\n)', text, re.M | re.S)
    parts = ['# Подсказки к уроку ' + str(lesson['number']) + '. ' + lesson['title'], '']
    if where:
        parts += [where.group(0), '']
    targets = ', '.join(f'`{file}` -> `{name}`' for file, name in lesson['targets'])
    parts += ['Текущее задание: ' + targets + '. Полный текст урока: course/' + Path(lesson['path']).name
              + ' в репозитории курса.', '']
    for section in re.split(r'(?m)^(?=## )', text):
        heading = section.splitlines()[0][3:] if section.startswith('## ') else ''
        if heading.startswith(TASK_SECTIONS):
            parts.append(section.strip())
            parts.append('')
    return plain_text('\n'.join(parts)).strip() + '\n'


def assemble(lesson: dict, config: dict, vault: Path | None) -> dict[str, bytes]:
    root = lesson['root']
    files = {}
    for path in sorted((STARTERS / root).rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            files[path.relative_to(STARTERS / root).as_posix()] = path.read_bytes()
    if not lesson.get('own_runtime'):
        files['local_llm.py'] = RUNTIME.read_bytes()
    for name, source in lesson.get('shared', {}).items():
        text = (STARTERS / source / name).read_text(encoding='utf-8')
        files[name] = solved_file(source, name, text).encode('utf-8')
    files['get_models.py'] = GET_MODELS.format(models=lesson['models']).encode('utf-8')
    lines = [line for group in lesson['requirements'] for line in config['requirements'][group]]
    files['requirements.txt'] = ('\n'.join(lines) + '\n').encode('utf-8')
    files['.gitignore'] = GITIGNORE.encode('utf-8')
    if vault:
        note = vault / config['course'] / next(d['source'] for d in config['documents'] if d['path'] == lesson['path'])
        files['TASK.md'] = task_text(lesson, note).encode('utf-8')
    else:
        files['TASK.md'] = 'Подсказки собираются из текста урока.\n'.encode('utf-8')
    return files


def write_zip(destination: Path, root: str, files: dict[str, bytes]) -> None:
    """Фиксированная дата внутри архива: при неизменных файлах ZIP не меняется побайтово."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, 'w', ZIP_DEFLATED) as archive:
        for name in sorted(files):
            info = ZipInfo(f'{root}/{name}', date_time=(2026, 10, 22, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, files[name])


def unpack(folder: Path, files: dict[str, bytes]) -> None:
    if folder.exists():
        shutil.rmtree(folder)
    for name, data in files.items():
        target = folder / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault', type=Path, help='Корень хранилища Obsidian: ZIP запишутся в папку материалов')
    parser.add_argument('--out', type=Path, help='Папка для распакованных каркасов (проверка без Obsidian)')
    args = parser.parse_args()
    config = load_config()
    for lesson in config['lessons']:
        files = assemble(lesson, config, args.vault)
        if args.vault:
            write_zip(args.vault / config['materials'] / (lesson['root'] + '.zip'), lesson['root'], files)
        if args.out:
            unpack(args.out / lesson['root'], files)
        print(lesson['root'], len(files), 'файлов')


if __name__ == '__main__':
    main()
