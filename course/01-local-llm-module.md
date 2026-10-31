# Дополнительно: Как устроен модуль local_llm.py

> **Для кого этот материал:** Модуль `local_llm.py` - это фундамент всей второй ступени курса. Он присутствует во всех 7 уроках и отвечает за скачивание файлов с HuggingFace, инициализацию C++ движка `llama-cpp-python`, управление оперативной памятью, очистку вывода и вызовы моделей.
> 
> Здесь мы подробно разберём каждую строчку этого файла, чтобы вы точно понимали, как работает локальный инференс под капотом Python.

---

## 1. Реестр моделей и константы

В самом верху файла задан словарь `MODELS`:

```python
HF = 'https://huggingface.co/'
MODELS = {
    'chat': ('Qwen3-1.7B-Q8_0.gguf', HF + 'Qwen/Qwen3-1.7B-GGUF/resolve/main/Qwen3-1.7B-Q8_0.gguf', 1834),
    'chat-small': ('Qwen3-0.6B-Q8_0.gguf', HF + 'Qwen/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q8_0.gguf', 639),
    'embed': ('Qwen3-Embedding-0.6B-Q8_0.gguf', HF + 'Qwen/Qwen3-Embedding-0.6B-GGUF/resolve/main/Qwen3-Embedding-0.6B-Q8_0.gguf', 639),
    'vision': ('Qwen3VL-2B-Instruct-Q4_K_M.gguf', HF + 'Qwen/Qwen3-VL-2B-Instruct-GGUF/resolve/main/Qwen3VL-2B-Instruct-Q4_K_M.gguf', 1107),
    'vision-proj': ('mmproj-Qwen3VL-2B-Instruct-Q8_0.gguf', HF + 'Qwen/Qwen3-VL-2B-Instruct-GGUF/resolve/main/mmproj-Qwen3VL-2B-Instruct-Q8_0.gguf', 445),
    'speech': ('ggml-small.bin', HF + 'ggerganov/whisper.cpp/resolve/main/ggml-small.bin', 488),
}
```

Каждая запись - это кортеж из трёх элементов:
1. Локальное имя файла на диске.
2. Прямой URL-адрес для скачивания с HuggingFace.
3. Примерный размер файла в мегабайтах (для отображения пользователю).

### Настройки сэмплирования (выбора токенов):
```python
SAMPLING = {'temperature': 0.7, 'top_p': 0.8, 'top_k': 20, 'min_p': 0.0, 'presence_penalty': 1.5}
NO_THINK = ' /no_think'
```

* `temperature = 0.7`: контролирует степень вариативности ответа. Чем ниже температура, тем ответ детерминированнее и строже.
* `top_p` и `top_k`: отсекают маловероятные "хвосты" токенов, защищая от бредогенерации.
* `presence_penalty = 1.5`: штрафует модель за повторение одних и тех же фраз.
* `NO_THINK = ' /no_think'`: специальный флаг для моделей семейства Qwen3, который отключает затяжной внутренний монолог (`<think>...`) и заставляет модель сразу выдавать полезный ответ клиенту.

---

## 2. Где хранятся модели: функции models_dir и require

```python
def models_dir() -> Path:
    folder = os.environ.get('AGENT_MODELS_DIR')
    return Path(folder) if folder else Path.home() / 'agent-models'
```

* `Path.home()` возвращает путь к домашней папке пользователя (например, `C:\Users\Имя`).
* Модели скачиваются в `C:\Users\Имя\agent-models`.
* Если у вас мало места на системном диске `C:`, вы можете задать переменную окружения `AGENT_MODELS_DIR=D:\agent-models`, и функция автоматически перенаправит хранилище на другой диск!

```python
def require(name: str) -> Path:
    path = model_path(name)
    if not path.is_file():
        raise FileNotFoundError(f'Нет файла модели {path.name} в папке {path.parent}. '
                                f'Запустите get_models.py этого урока.')
    return path
```
* Функция проверяет, действительно ли файл модели существует на диске перед тем, как пытаться скормить его C++ движку. Если файла нет, она выдаёт понятную подсказку: "Запустите `get_models.py`".

---

## 3. Фоновая докачка: функция download

```python
def download(*names: str) -> None:
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
```

### Архитектурная фишка с `.part`:
Обратите внимание: файл скачивается во временное имя `filename + '.part'`. И только когда `urllib.request.urlretrieve` успешно завершит 100% загрузки, происходит переименование `partial.replace(target)`.

Зачем так сделано?
Если интернет оборвётся на 80%, в папке не останется битого файла с нормальным именем. При следующем запуске скрипт поймёт, что целевого файла нет, и перезапустит загрузку, вместо того чтобы пытаться загрузить в память обрезанный файл.

---

## 4. Управление памятью: контекстный менеджер load_chat

```python
from contextlib import contextmanager

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
        model.close()
```

### Как работает `@contextmanager`?
1. До строчки `yield model` выполняется подготовка: проверяется путь и создаётся тяжелый объект `Llama(...)`.
   * `n_ctx=4096` - размер окна контекста (максимум токенов в памяти).
   * `n_gpu_layers=0` - принудительно оставляем все вычисления на CPU (процессоре), не требуя видеокарту.
   * `seed=42` - фиксируем генератор случайных чисел для повторяемости тестов.
2. `yield model`: управление передаётся наружу в ваш блок `with load_chat() as model:`. Вы работаете с моделью: вызываете `ask(model, ...)`.
3. Блок `finally: model.close()`: как только блок `with` заканчивается, Python немедленно вызывает C++ метод закрытия дескрипторов и освобождает 1,8 ГБ оперативной памяти.

---

## 5. Очистка ответа: функция clean_answer

```python
def clean_answer(response: dict) -> str:
    choice = response['choices'][0]
    if choice.get('finish_reason') != 'stop':
        raise ValueError('Генерация не завершена: модель упёрлась в лимит max_tokens')
    text = choice['message'].get('content')
    if not isinstance(text, str):
        raise ValueError('Модель не вернула текст')
    text = re.sub(r'\A\s*<think>.*?</think>\s*', '', text, flags=re.S).strip()
    if not text:
        raise ValueError('Модель вернула пустой ответ')
    return text
```

1. Проверяет `finish_reason == 'stop'`: если генерация оборвалась из-за нехватки лимита `max_tokens`, функция не отдаёт обрезанный текст, а сигнализирует об ошибке.
2. Регулярное выражение `re.sub(r'\A\s*<think>.*?</think>\s*', '', text)` аккуратно срезает пустые служебные блоки размышлений, которые иногда оставляет модель Qwen.
3. Возвращает гарантированно непустую строку.

---

## 6. Главная рабочая функция: ask

```python
def ask(model, instruction: str, text: str, schema: dict | None = None, max_tokens: int = 256):
    settings = dict(SAMPLING, max_tokens=max_tokens)
    if schema is not None:
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
```

Это именно та функция, которую вы пишете в Уроке 1 и которая затем используется во всех уроках второй ступени:
* Она собирает правильный диалог: `system` (правило) и `user` (входные данные).
* Если передана `schema`, она активирует режим грамматического фильтра C++ движка (`response_format`) и распарсивает JSON перед возвратом.
* Если схемы нет, она возвращает чистый текст.

---

Вернуться к:
* [Уроку 1. Модель внутри программы](01-model-in-process.md)
* [Оглавлению второй ступени](README.md)
