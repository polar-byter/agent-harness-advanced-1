"""Собрать архив независимого учебного примера без моделей и окружения."""

import argparse
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vault', type=Path, required=True)
    args = parser.parse_args()
    source = ROOT / 'maintainer/fine_tuning_demo'
    target = args.vault / 'Agent Harness Advanced 1/Уроки/Материалы/fine-tuning-dialogues.zip'
    target.parent.mkdir(parents=True, exist_ok=True)
    allowed_suffixes = {'.py', '.md', '.json', '.jsonl', '.txt'}
    with ZipFile(target, 'w', compression=ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob('*')):
            relative = path.relative_to(source)
            if not path.is_file() or any(part.startswith('.') or part == '__pycache__' for part in relative.parts[:-1]):
                continue
            if path.suffix not in allowed_suffixes and path.name != '.gitignore':
                continue
            if relative.parts[0] in {'models', 'runs', 'data-rebuilt'}:
                continue
            member = ZipInfo('fine-tuning-dialogues/' + relative.as_posix(), (1980, 1, 1, 0, 0, 0))
            member.compress_type = ZIP_DEFLATED
            archive.writestr(member, path.read_bytes().replace(b'\r\n', b'\n'))
    print('Архив учебного примера собран:', target.name)


if __name__ == '__main__':
    main()
