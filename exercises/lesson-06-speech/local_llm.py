"""Общий модуль курса: где лежат файлы моделей, как их скачать и загрузить в программу.

Один и тот же файл лежит во всех каркасах. Библиотеки моделей импортируются внутри функций,
поэтому проверки без модели работают даже там, где llama-cpp-python ещё не установлен.
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import urllib.request

HF = 'https://huggingface.co/'
# Имя в программе -> (файл, адрес, примерный размер в МБ).
MODELS = {
    'chat': ('Qwen3-1.7B-Q8_0.gguf', HF + 'Qwen/Qwen3-1.7B-GGUF/resolve/main/Qwen3-1.7B-Q8_0.gguf', 1834),
    'chat-small': ('Qwen3-0.6B-Q8_0.gguf', HF + 'Qwen/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q8_0.gguf', 639),
    'embed': ('Qwen3-Embedding-0.6B-Q8_0.gguf',
              HF + 'Qwen/Qwen3-Embedding-0.6B-GGUF/resolve/main/Qwen3-Embedding-0.6B-Q8_0.gguf', 639),
    'vision': ('Qwen3VL-2B-Instruct-Q4_K_M.gguf',
               HF + 'Qwen/Qwen3-VL-2B-Instruct-GGUF/resolve/main/Qwen3VL-2B-Instruct-Q4_K_M.gguf', 1107),
    'vision-proj': ('mmproj-Qwen3VL-2B-Instruct-Q8_0.gguf',
                    HF + 'Qwen/Qwen3-VL-2B-Instruct-GGUF/resolve/main/mmproj-Qwen3VL-2B-Instruct-Q8_0.gguf', 445),
    'speech': ('ggml-small.bin', HF + 'ggerganov/whisper.cpp/resolve/main/ggml-small.bin', 488),
}

# Настройки выбора токенов из карточки Qwen3 для режима без рассуждений.
SAMPLING = {'temperature': 0.7, 'top_p': 0.8, 'top_k': 20, 'min_p': 0.0, 'presence_penalty': 1.5}
# Команда Qwen3: отвечать сразу, без развёрнутого блока рассуждений.
NO_THINK = ' /no_think'
_quiet_log = None  # ссылку на функцию журнала храним, пока работает модель зрения


def models_dir() -> Path:
    """Одна папка моделей на компьютер: файлы не скачиваются заново для каждого урока."""
    folder = os.environ.get('AGENT_MODELS_DIR')
    return Path(folder) if folder else Path.home() / 'agent-models'


def model_path(name: str) -> Path:
    return models_dir() / MODELS[name][0]


def require(name: str) -> Path:
    path = model_path(name)
    if not path.is_file():
        raise FileNotFoundError(f'Нет файла модели {path.name} в папке {path.parent}. '
                                f'Запустите get_models.py этого урока.')
    return path


def download(*names: str) -> None:
    """Скачиваем недостающие файлы. Пока загрузка не закончилась, файл называется *.part."""
    folder = models_dir()
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        filename, url, size = MODELS[name]
        target = folder / filename
        if target.is_file():
            print(f'{filename}: уже скачан')
            continue
        print(f'{filename}: скачиваем около {size} МБ в {folder}')
        partial = target.with_name(filename + '.part')

        def progress(blocks, block_size, total):
            if total > 0 and blocks % 2000 == 0:
                print(f'  {min(100, blocks * block_size * 100 // total)}%')

        urllib.request.urlretrieve(url, partial, progress)
        partial.replace(target)
        print(f'{filename}: готово')


def chat_model_name() -> str:
    """Берём основную модель, а если скачана только маленькая - её."""
    if model_path('chat').is_file() or not model_path('chat-small').is_file():
        return 'chat'
    return 'chat-small'


@contextmanager
def load_chat(name: str | None = None, n_ctx: int = 4096):
    name = name or chat_model_name()
    path = require(name)
    from llama_cpp import Llama
    print(f'Загружаем {path.name}...')
    model = Llama(model_path=str(path), n_ctx=n_ctx, n_gpu_layers=0, seed=42, verbose=False)
    try:
        yield model
    finally:
        # Llama этой версии не поддерживает with, поэтому память освобождаем сами.
        model.close()


@contextmanager
def load_embedder():
    path = require('embed')
    from llama_cpp import Llama
    print(f'Загружаем {path.name}...')
    model = Llama(model_path=str(path), embedding=True, n_ctx=512, n_gpu_layers=0, verbose=False)
    try:
        yield model
    finally:
        model.close()


@contextmanager
def load_vision():
    path, projector = require('vision'), require('vision-proj')
    import llama_cpp
    import llama_cpp.mtmd_cpp as mtmd
    from llama_cpp import Llama
    from llama_cpp.llama_chat_format import MTMDChatHandler
    global _quiet_log
    # Обработчик картинок печатает подробный журнал даже при verbose=False; отключаем его.
    _quiet_log = llama_cpp.llama_log_callback(lambda level, text, data: None)
    mtmd.mtmd_log_set(_quiet_log, None)
    mtmd.mtmd_helper_log_set(_quiet_log, None)
    print(f'Загружаем {path.name} и {projector.name}...')
    # Проектор переводит картинку в векторы, понятные языковой части модели.
    handler = MTMDChatHandler(clip_model_path=str(projector), verbose=False, use_gpu=False)
    model = Llama(model_path=str(path), chat_handler=handler, n_ctx=4096, n_gpu_layers=0, verbose=False)
    try:
        yield model
    finally:
        model.close()


@contextmanager
def load_speech():
    path = require('speech')
    from pywhispercpp.model import Model
    print(f'Загружаем {path.name}...')
    yield Model(str(path), redirect_whispercpp_logs_to=None, print_progress=False,
                n_threads=min(8, os.cpu_count() or 4))


def clean_answer(response: dict) -> str:
    """Достаём текст из ответа create_chat_completion и проверяем, что генерация завершилась."""
    choice = response['choices'][0]
    if choice.get('finish_reason') != 'stop':
        raise ValueError('Генерация не завершена: модель упёрлась в лимит max_tokens')
    text = choice['message'].get('content')
    if not isinstance(text, str):
        raise ValueError('Модель не вернула текст')
    # Qwen3 может поставить пустой служебный блок перед ответом.
    text = re.sub(r'\A\s*<think>.*?</think>\s*', '', text, flags=re.S).strip()
    if not text:
        raise ValueError('Модель вернула пустой ответ')
    return text


def ask(model, instruction: str, text: str, schema: dict | None = None, max_tokens: int = 256):
    """Одно обращение к языковой модели: правило, данные и, если нужно, схема JSON."""
    settings = dict(SAMPLING, max_tokens=max_tokens)
    if schema is not None:
        # Схема ограничивает выбор токенов: модель может написать только такой JSON.
        settings['response_format'] = {'type': 'json_object', 'schema': schema}
    messages = [
        {'role': 'system', 'content': instruction + NO_THINK},
        {'role': 'user', 'content': text},
    ]
    response = model.create_chat_completion(messages=messages, **settings)
    answer = clean_answer(response)
    if schema is not None:
        return json.loads(answer)
    return answer
