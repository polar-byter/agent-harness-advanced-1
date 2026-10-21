# Каталог фильмов: модель в веб-сервисе

Готовый локальный сервис на Flask: список фильмов, фильтр по тегам, поиск, добавление фильма.
Задание - внедрить в него поиск по смыслу на модели эмбеддингов из урока 3.

```text
web.py         веб-слой: адреса и страницы
service.py     правила каталога: CatalogService
repository.py  хранение в SQLite: MovieRepository
search.py      способы поиска: KeywordSearch и SemanticSearch
run.py         точка сборки: что с чем соединить и запустить
```

1. Откройте эту папку в PyCharm через File -> Open и выберите общий интерпретатор курса.
2. Установите зависимости: `python -m pip install --only-binary=:all: -r requirements.txt`.
3. Запустите run.py и откройте http://127.0.0.1:5000 в браузере. Остановить сервер: красный квадрат Stop в Run.
4. Допишите SemanticSearch.find в search.py и подключите его в run.py по TASK.md.
5. Запустите demo_check.py, затем demo.py и снова run.py.

После реализации demo_check.py выводит:

```text
Проверка без модели: путешествие во времени -> Гостья из будущего
```

Проверки: tests/test_lesson.py -> class LessonTests -> Run.
