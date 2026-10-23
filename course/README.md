# Все уроки и каркасы

Вторая ступень [основного курса "Агентная мастерская"](https://github.com/polar-byter/agent-harness-workshop/blob/main/course/README.md). Начните с [вводной](00-introduction.md): в ней объяснено, что мы берём из основного курса и что нового.

Уроки лучше проходить по порядку: в первом создаётся общее окружение Python и скачивается языковая модель, второй и седьмой работают с одним журналом, третий продолжает идею схемы ответа из второго. Но каждый каркас самостоятелен: всё, что написано в прошлых уроках, в нём уже готово.

| Урок | Каркас | Модели | Новые библиотеки |
|---|---|---|---|
| [1. Модель внутри программы](01-model-in-process.md) | [lesson-01-runtime](../downloads/lesson-01-runtime.zip?raw=true) | Qwen3-1.7B, 1,8 ГБ | llama-cpp-python |
| [2. Журнал проделок кота](02-cat-journal.md) | [lesson-02-cat-journal](../downloads/lesson-02-cat-journal.zip?raw=true) | Qwen3-1.7B | openpyxl |
| [3. Модель, которая принимает решения](03-decisions.md) | [lesson-03-decisions](../downloads/lesson-03-decisions.zip?raw=true) | Qwen3-1.7B | - |
| [4. Модель зрения проверяет фото](04-vision.md) | [lesson-04-vision](../downloads/lesson-04-vision.zip?raw=true) | Qwen3-VL-2B, 1,6 ГБ | - |
| [5. Модель в веб-сервисе](05-movie-service.md) | [lesson-05-movie-service](../downloads/lesson-05-movie-service.zip?raw=true) | Qwen3-Embedding-0.6B, 640 МБ | Flask |
| [6. Расшифровка голосового сообщения](06-speech.md) | [lesson-06-speech](../downloads/lesson-06-speech.zip?raw=true) | Whisper small, 490 МБ; Qwen3-1.7B | pywhispercpp |
| [7. Telegram-бот](07-telegram-bot.md) | [lesson-07-telegram-bot](../downloads/lesson-07-telegram-bot.zip?raw=true) | Qwen3-1.7B | pyTelegramBotAPI |

Итоги и опубликованные кейсы - в [заключении](conclusion.md).

## Как работать с каркасом

Скачайте архив урока, распакуйте через **Извлечь всё** и откройте папку урока в PyCharm через **File -> Open**. Выберите общее окружение курса `C:\Users\Имя\agent-venv` (зачем оно, как его создать и когда можно обойтись без него, описано в первом уроке) и установите зависимости командой из урока. Модели лежат в общей папке `C:\Users\Имя\agent-models`, а `get_models.py` в каждом каркасе скачивает только недостающие.

В каждом каркасе есть:

- `TASK.md` - подсказки к текущему заданию, собранные из текста урока;
- `local_llm.py` - общий модуль загрузки моделей, одинаковый во всех уроках начиная со второго;
- `demo_check.py` - проверка вашей функции на подставном объекте вместо модели, работает без скачанных моделей;
- `demo.py` - запуск с настоящей моделью;
- `tests/test_lesson.py` - готовые тесты: откройте файл и запустите `class LessonTests`.

До того как вы допишете функцию, `demo_check.py` и `demo.py` выводят подсказку `Допишите ...`, а тесты закономерно не проходят.
