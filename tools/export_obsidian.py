"""Выгружаем читательский курс из Obsidian: уроки, схемы, архивы и распакованные каркасы.

Файлы, изменённые в репозитории вручную, экспорт не перезаписывает: сначала перенесите правку в Obsidian.
"""
import argparse
import hashlib
import html
import json
import os
import re
from pathlib import Path
from urllib.parse import quote
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PLAIN = {'—': '-', '–': '-', '→': '->', '←': '<-', '…': '...', '\xa0': ' ', '\xab': '"',
         '\xbb': '"', '“': '"', '”': '"', '„': '"', '‘': "'", '’': "'", '−': '-',
         '•': '-', '\xd7': '*', ' ': ' '}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def plain_punctuation(text: str) -> str:
    for old, new in PLAIN.items():
        text = text.replace(old, new)
    return text


def relative_link(source: Path, target: Path) -> str:
    return quote(os.path.relpath(target, source.parent).replace('\\', '/'), safe='/.-_')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault', type=Path, required=True, help='Корень хранилища Obsidian')
    args = parser.parse_args()
    vault = args.vault.resolve()
    config = json.loads((ROOT / 'tools' / 'course-map.json').read_text(encoding='utf-8'))
    course, materials = config['course'], config['materials']
    manifest_path = ROOT / 'maintainer' / 'export-manifest.json'
    previous = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {'files': {}}
    # Ключ - путь от корня хранилища без .md, как его пишут в wiki-ссылках.
    mapping = {course + '/' + item['source'][:-3]: item['path'] for item in config['documents']}
    for lesson in config['lessons']:
        mapping[materials + '/' + lesson['root'] + '.zip'] = 'downloads/' + lesson['root'] + '.zip'
    pending = {}

    def stage(relative: str, data: bytes) -> None:
        if Path(relative).suffix in ('.md', '.py', '.json', '.txt', '.html') or Path(relative).name == '.gitignore':
            data = data.replace(b'\r\n', b'\n')
        target = ROOT / relative
        if target.exists():
            current = target.read_bytes()
            known = previous['files'].get(relative)
            if current != data and (known is None or digest(current) != known):
                raise ValueError('Файл изменён вручную; экспорт его не перезаписал: ' + relative)
        pending[relative] = data

    def convert(text: str, destination: str) -> str:
        text = re.sub(r'\A---\n.*?\n---\n', '', text.replace('\r\n', '\n'), count=1, flags=re.S).lstrip()

        def collapse(match):
            inner = re.sub(r'^> ?', '', match.group(2), flags=re.M).strip()
            return '<details>\n<summary>' + html.escape(match.group(1).strip()) + '</summary>\n\n' + inner + '\n\n</details>\n'
        text = re.sub(r'^> \[!\w+\]-\s*(.*?)\n((?:>.*(?:\n|$))+)', collapse, text, flags=re.M)

        def link(match):
            embedded, raw, label = match.groups()
            source = raw.rstrip('\\')  # в таблицах Obsidian разделитель подписи пишется как \|
            if embedded:
                target = 'assets/' + Path(source).name
                assets[source] = target
                width = int(label) if label and label.isdigit() else 480
                url = relative_link(Path(destination), Path(target))
                return f'<img src="{html.escape(url)}" width="{width}" alt="{html.escape(Path(source).stem)}">'
            if source not in mapping:
                raise ValueError('Нет читательского назначения для ссылки: ' + raw)
            url = relative_link(Path(destination), Path(mapping[source]))
            if url.endswith('.zip'):
                url += '?raw=true'
            return '[' + (label or Path(source).stem) + '](' + url + ')'
        text = re.sub(r'(!?)\[\[([^\]|]+)(?:\|([^\]]*))?\]\]', link, text)
        return plain_punctuation(text.strip()) + '\n'

    assets = {}
    lessons = {lesson['path']: lesson for lesson in config['lessons']}
    for document in config['documents']:
        destination = document['path']
        text = convert((vault / course / document['source']).read_text(encoding='utf-8'), destination)
        lesson = lessons.get(destination)
        if lesson:
            local = Path('exercises') / lesson['root']
            links = ('[Исходники урока](' + relative_link(Path(destination), local / 'README.md') + ') / '
                     '[Подсказки рядом с кодом](' + relative_link(Path(destination), local / 'TASK.md') + ')')
            heading, _, rest = text.partition('\n\n')
            text = heading + '\n\n' + links + '\n\n' + rest
        stage(destination, text.encode('utf-8'))
    for source, destination in assets.items():
        stage(destination, (vault / source).read_bytes())
    for lesson in config['lessons']:
        archive_path = vault / materials / (lesson['root'] + '.zip')
        stage('downloads/' + lesson['root'] + '.zip', archive_path.read_bytes())
        with ZipFile(archive_path) as archive:
            assert archive.testzip() is None
            for name in archive.namelist():
                parts = Path(name).parts
                if not parts or parts[0] != lesson['root'] or '..' in parts:
                    raise ValueError('Недопустимый путь в архиве: ' + name)
                if name.endswith('/') or len(parts) == 1:
                    continue
                relative = Path(*parts[1:])
                target = (Path('exercises') / lesson['root'] / relative).as_posix()
                content = archive.read(name)
                if relative.as_posix() == 'README.md':
                    back = relative_link(Path(target), Path(lesson['path']))
                    content = (f'[Урок {lesson["number"]}. {lesson["title"]}]({back}) / '
                               '[Все уроки](../../course/README.md)\n\n').encode('utf-8') + content
                stage(target, content)
    for relative, data in pending.items():
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    manifest = {'format': 1, 'source': 'Obsidian: только читательский курс', 'documents': len(config['documents']),
                'lessons': len(config['lessons']), 'files': {key: digest(value) for key, value in sorted(pending.items())}}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Выгружено:', len(config['documents']), 'страниц,', len(config['lessons']), 'каркасов,', len(assets), 'схем')


if __name__ == '__main__':
    main()
