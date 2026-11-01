"""Проверить архив и синтетические данные дополнения без запуска нейросети."""

import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import textwrap
import unicodedata
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / 'maintainer/fine_tuning_demo'
    subprocess.run([sys.executable, '-B', str(source / 'check_data.py')], check=True)
    manifest = json.loads((source / 'data/manifest.json').read_text(encoding='utf-8'))
    for name, expected_hash in manifest['sha256'].items():
        assert hashlib.sha256((source / 'data' / name).read_bytes()).hexdigest() == expected_hash, name
    for path in source.glob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    archive_path = ROOT / 'downloads/fine-tuning-dialogues.zip'
    with ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        archived_manifest = json.loads(archive.read('fine-tuning-dialogues/data/manifest.json'))
        for name, expected_hash in archived_manifest['sha256'].items():
            assert hashlib.sha256(archive.read('fine-tuning-dialogues/data/' + name)).hexdigest() == expected_hash, name
        for member in archive.namelist():
            relative = Path(member).relative_to('fine-tuning-dialogues')
            assert '..' not in relative.parts
            original = (source / relative).read_bytes().replace(b'\r\n', b'\n')
            assert archive.read(member) == original, member
        count = len(archive.namelist())
    page = ROOT / 'course/fine-tuning-dialogues.md'
    text = page.read_text(encoding='utf-8')
    assert text.count('```') % 2 == 0
    assert not {char for char in text if ord(char) > 127 and unicodedata.category(char)[0] in 'PSZ'}
    for code in re.findall(r'```python\n(.*?)```', text, re.S):
        ast.parse(textwrap.dedent(code), filename=str(page))
    for target in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', text):
        url = urlsplit(target)
        if not url.scheme and url.path:
            resolved = (page.parent / unquote(url.path)).resolve()
            assert resolved.is_relative_to(ROOT) and resolved.exists(), target
    print('Учебный пакет проверен. Файлов в архиве:', count)
    print('Обучение модели и оценка ее качества не выполнялись')


if __name__ == '__main__':
    main()
