[Урок 5. Модель в веб-сервисе](../../course/05-movie-service.md) / [Все уроки](../../course/README.md)

# Каталог фильмов: модель в веб-сервисе

Готовый локальный сервис на Flask: список фильмов, фильтр по тегам, поиск, добавление фильма.
Задание - внедрить в него поиск по смыслу на модели эмбеддингов Qwen3-Embedding.

```text
web.py         веб-слой: адреса и страницы
service.py     правила каталога: CatalogService
repository.py  хранение в SQLite: MovieRepository
search.py      способы поиска: KeywordSearch и SemanticSearch
run.py         точка сборки: что с чем соединить и запустить
```

1. Откройте эту папку в PyCharm через File -> Open и выберите общий интерпретатор курса.
2. Установите зависимости: `python -m pip install --only-binary=:all: -r requirements.txt`.
3. В дереве проекта щёлкните правой кнопкой по get_models.py и выберите Run 'get_models': скачается модель эмбеддингов, около 640 МБ.
4. В дереве проекта щёлкните правой кнопкой по run.py и выберите Run 'run', затем откройте http://127.0.0.1:5000 в браузере. Остановить сервер: красный квадрат Stop в Run.
5. Допишите SemanticSearch.find в search.py и подключите его в run.py по TASK.md.
6. Запустите demo_check.py, затем demo.py и снова run.py.

После реализации demo_check.py выводит:

```text
Проверка без модели: путешествие во времени -> Гостья из будущего
```

Проверки: tests/test_lesson.py -> class LessonTests -> Run.
