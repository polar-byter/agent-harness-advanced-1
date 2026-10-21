# Голосовое сообщение клиента

Whisper расшифровывает запись на процессоре, а языковая модель заполняет по расшифровке
карточку обращения. Учебная запись data/call.wav синтезирована голосом Windows.

1. Откройте эту папку в PyCharm через File -> Open и выберите общий интерпретатор курса.
2. Установите зависимости: `python -m pip install --only-binary=:all: -r requirements.txt`.
3. Запустите get_models.py: скачается Whisper small, около 490 МБ.
4. Допишите transcribe в speech.py по TASK.md.
5. Запустите demo_check.py, затем demo.py.

После реализации demo_check.py выводит:

```text
Проверка без модели: [00:07] Две недели назад я купила у вас электрический чайник,
```

Проверки: tests/test_lesson.py -> class LessonTests -> Run.
