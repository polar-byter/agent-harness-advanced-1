# Telegram-бот для журнала кота

Бот принимает от членов семьи сообщения о проделках кота, разбирает их локальной моделью
и записывает в тот же журнал Excel, что и утилита из урока 2.

```text
bot_logic.py   что ответить на сообщение; здесь нет ничего от Telegram
bot.py         подключение к Telegram: токен, обработчики, long polling
journal_ai.py  разбор записи моделью (готово из урока 2)
journal_io.py  чтение и запись Excel (готово из урока 2)
```

1. Откройте эту папку в PyCharm через File -> Open и выберите общий интерпретатор курса.
2. Установите зависимости: `python -m pip install --only-binary=:all: -r requirements.txt`.
3. Допишите handle_text в bot_logic.py по TASK.md.
4. Запустите demo_check.py, затем demo.py: это разговор с ботом без Telegram.
5. Создайте бота у @BotFather, сохраните токен по инструкции урока и запустите bot.py.

После реализации demo_check.py выводит:

```text
Проверка без модели: Записал в журнал: кухня, серьёзность 1.
```

Проверки: tests/test_lesson.py -> class LessonTests -> Run.
