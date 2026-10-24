"""Те же вопросы открытой модели решений FRIDA-Decisions от Сбера: она работает на процессоре без сети.

Библиотеку ставят отдельно, она нужна только этому варианту урока:
python -m pip install --only-binary=:all: "frida-decisions[onnx] @ https://github.com/ai-forever/FRIDA-Decisions/archive/refs/tags/v0.4.0.zip"
Импорт идёт внутри load_frida, поэтому проверки без модели работают и без библиотеки.
"""
from local_llm import models_dir

REPO = 'ai-forever/FRIDA-Decisions'
# Для процессора нужны настройки модели и сжатый до 8 бит граф ONNX, около 1,2 ГБ.
FILES = ['*.json', 'onnx/*']


def frida_dir():
    return models_dir() / 'FRIDA-Decisions'


def load_frida(threads: int = 4):
    """Скачиваем недостающие файлы в общую папку моделей и загружаем модель."""
    from huggingface_hub import snapshot_download
    from frida_decisions import OnnxJudge

    folder = frida_dir()
    print('FRIDA-Decisions: проверяем файлы в', folder, '(при первом запуске скачивается около 1,2 ГБ)')
    snapshot_download(REPO, allow_patterns=FILES, local_dir=folder)
    return OnnxJudge.from_pretrained(folder, threads=threads)


def ask_frida(judge, state: str, questions: dict) -> dict:
    """Запрос в том же формате, что у Jev, и ответы с теми же ключами, что у decide."""
    return judge.judge({'state': state, 'questions': questions})['answers']
