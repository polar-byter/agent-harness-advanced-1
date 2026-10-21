"""Проверяем упаковку курса без моделей и без сети.

Ссылки и пунктуация в Markdown, синтаксис Python, совпадение архивов с папками exercises,
общий модуль local_llm.py, незавершённые demo_check.py и demo.py. Успех не означает,
что учебные функции реализованы: для эталонов есть tools/check_solutions.py.
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile

from build_starters import solved_file

ROOT = Path(__file__).resolve().parents[1]
SKIP = ('.git', '.checks', '.venv', 'maintainer')
TEXT = ('.py', '.md', '.json', '.txt', '.html')


def check_markdown() -> tuple[int, int]:
    files = [path for path in ROOT.rglob('*.md') if not any(part in SKIP for part in path.relative_to(ROOT).parts)]
    files += [ROOT / 'maintainer' / name for name in ('README.md', 'WORK_LOG.md')]
    links = 0
    for path in files:
        text = path.read_text(encoding='utf-8')
        special = sorted({char for char in text if ord(char) > 127 and unicodedata.category(char)[0] in 'PSZ'})
        assert not special, (path, 'Только клавиатурная пунктуация', special)
        assert not re.search(r'\[\[[^\]\n]+\]\]', text), (path, 'Осталась ссылка Obsidian')
        assert text.count('```') % 2 == 0, (path, 'Незакрытый блок кода')
        for code in re.findall(r'```python\n(.*?)```', text, re.S):
            # Заготовки показывают тело функции с отступом, поэтому снимаем общий отступ.
            ast.parse(textwrap.dedent(code), filename=str(path))
        targets = re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', text) + re.findall(r'<img[^>]+src="([^"]+)"', text)
        for target in targets:
            url = urlsplit(target)
            if url.scheme or url.netloc or not url.path:
                continue
            resolved = (path.parent / unquote(url.path)).resolve()
            assert resolved.is_relative_to(ROOT) and resolved.exists(), (path, target)
            links += 1
        for width in re.findall(r'<img[^>]+width="(\d+)"', text):
            assert int(width) <= 600, (path, width)
    return len(files), links


def normalized(data: bytes, name: str) -> bytes:
    return data.replace(b'\r\n', b'\n') if name.endswith(TEXT) or name.endswith('.gitignore') else data


def run(folder: Path, module: str) -> str:
    result = subprocess.run([sys.executable, '-B', '-c', f'import {module}; {module}.main()'], cwd=folder,
                            capture_output=True, text=True, encoding='utf-8', timeout=60,
                            env=dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1'))
    assert result.returncode == 0, (folder.name, module, result.stdout, result.stderr)
    return result.stdout


def main():
    config = json.loads((ROOT / 'tools' / 'course-map.json').read_text(encoding='utf-8'))
    for document in config['documents']:
        assert (ROOT / document['path']).is_file(), document['path']
    pages, links = check_markdown()
    runtime = (ROOT / 'tools' / 'model_runtime' / 'local_llm.py').read_bytes()
    python_files = 0
    scratch = ROOT / '.checks'
    scratch.mkdir(exist_ok=True)
    for lesson in config['lessons']:
        exercise = ROOT / 'exercises' / lesson['root']
        assert (exercise / 'TASK.md').is_file() and (exercise / 'tests' / 'test_lesson.py').is_file(), lesson['root']
        for path in exercise.rglob('*.py'):
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
            python_files += 1
        archived = set()
        with ZipFile(ROOT / 'downloads' / (lesson['root'] + '.zip')) as package:
            assert package.testzip() is None, lesson['root']
            for name in package.namelist():
                relative = Path(*Path(name).parts[1:]).as_posix()
                archived.add(relative)
                if relative != 'README.md':
                    assert normalized(package.read(name), name) == normalized((exercise / relative).read_bytes(), name), \
                        (lesson['root'], relative, 'архив и папка exercises различаются')
        unpacked = {path.relative_to(exercise).as_posix() for path in exercise.rglob('*') if path.is_file()
                    and '__pycache__' not in path.parts}
        assert unpacked == archived, (lesson['root'], 'лишние или недостающие файлы', unpacked ^ archived)
        lines = [line for group in lesson['requirements'] for line in config['requirements'][group]]
        assert (exercise / 'requirements.txt').read_text(encoding='utf-8').split() == ' '.join(lines).split()
        if not lesson.get('own_runtime'):
            assert (exercise / 'local_llm.py').read_bytes() == runtime, (lesson['root'], 'local_llm.py отличается')
        else:
            # В первом уроке модуль с заглушкой: эталонное решение должно вернуть общий модуль побайтово.
            stub = (exercise / 'local_llm.py').read_text(encoding='utf-8')
            assert solved_file(lesson['root'], 'local_llm.py', stub).encode('utf-8') == runtime, lesson['root']
        for file, name in lesson['targets']:
            assert name.split('.')[-1] in (exercise / file).read_text(encoding='utf-8'), (lesson['root'], file, name)
        demo_source = (exercise / 'demo.py').read_text(encoding='utf-8')
        assert 'Example' not in demo_source, (lesson['root'], 'demo.py должен работать с настоящей моделью')
        # Копия в .checks: проверка не создаёт файлов в папке упражнения.
        with tempfile.TemporaryDirectory(prefix=lesson['root'] + '-', dir=scratch) as folder:
            copy = Path(folder) / lesson['root']
            shutil.copytree(exercise, copy)
            for module in ('demo_check', 'demo'):
                output = run(copy, module)
                assert 'Допишите' in output, (lesson['root'], module, output)
        print(lesson['root'] + ': архив, каркас и незавершённые демо в порядке')
    shutil.rmtree(scratch, ignore_errors=True)
    print(f'Проверено: {pages} страниц, {links} локальных ссылок, {python_files} файлов Python, '
          f'{len(config["lessons"])} каркасов. Модели не загружались, сеть не использовалась.')
    subprocess.run([sys.executable, '-B', str(ROOT / 'tools' / 'test_model_runtime.py')], check=True)


if __name__ == '__main__':
    main()
