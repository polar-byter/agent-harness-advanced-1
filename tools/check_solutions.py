"""Проверяем каркасы с эталонными решениями во временных копиях. Модели не загружаются.

Эталоны лежат в maintainer/solutions и в каркасы читателя не попадают.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from build_starters import ROOT, SOLUTIONS, load_config, solved_file


def run(folder: Path, *command: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, '-B', *command], cwd=folder, capture_output=True, text=True,
                          encoding='utf-8', timeout=120,
                          env=dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'exercises')
    args = parser.parse_args()
    for lesson in load_config()['lessons']:
        with tempfile.TemporaryDirectory(prefix=lesson['root'] + '-') as folder:
            copy = Path(folder) / lesson['root']
            shutil.copytree(args.source / lesson['root'], copy)
            for solution in (SOLUTIONS / lesson['root']).iterdir():
                relative = solution.name.removesuffix('.txt')
                target = copy / relative
                target.write_text(solved_file(lesson['root'], relative, target.read_text(encoding='utf-8')),
                                  encoding='utf-8', newline='\n')
            tests = run(copy, 'tests/test_lesson.py')
            assert tests.returncode == 0, (lesson['root'], tests.stdout, tests.stderr)
            demo = run(copy, '-c', 'import demo_check; demo_check.main()')
            assert demo.returncode == 0 and lesson['expected'] in demo.stdout, (lesson['root'], demo.stdout, demo.stderr)
        print(lesson['root'] + ': решение проходит тесты, demo_check выводит ожидаемое')


if __name__ == '__main__':
    main()
