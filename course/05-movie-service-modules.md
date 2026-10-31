# Дополнительно: Как устроен веб-сервис каталога фильмов

> **Для кого этот материал:** В Уроке 5 мы встроили модель семантических эмбеддингов в работающий веб-сервис на Flask.
> 
> Здесь мы разберем все модули проекта и архитектурные паттерны: Репозиторий, Сервис, Стратегию и Внедрение зависимостей.

---

## 1. Слой данных: repository.py (Паттерн Репозиторий)

Класс `MovieRepository` изолирует все операции с базой данных SQLite:

```python
import sqlite3

class MovieRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    tags TEXT NOT NULL
                )
            ''')
```
* `sqlite3.connect(...)` как контекстный менеджер автоматически делает `commit()` транзакции при успешном выходе.
* Методы `all()` и `add()` преобразуют SQL-строки в удобные словари Python.
* Бизнес-логика ничего не знает о SQL - она просто вызывает `repo.all()`.

---

## 2. Слой домена: service.py (Бизнес-правила)

Класс `CatalogService` управляет правилами каталога:
* Проверяет непустоту названия и описания при добавлении фильма.
* Приводит теги к нижнему регистру и удаляет лишние пробелы.
* При вызове `service.search(query)` делегирует поиск объекту `self.search_strategy`.

---

## 3. Слой поиска: search.py (Паттерн Стратегия и Косинусное сходство)

### Вычисление косинусной близости:
```python
def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
```
Поскольку модель `Qwen3-Embedding` возвращает векторы единичной длины, косинус угла равен обычному скалярному произведению (dot product).

### Семантический поиск SemanticSearch:
```python
class SemanticSearch:
    def __init__(self, model):
        self.model = model
        self.vectors = {}  # Кэш векторов

    def movie_vector(self, movie: dict) -> list[float]:
        movie_id = movie['id']
        if movie_id not in self.vectors:
            text = f"{movie['title']}. {movie['description']}"
            self.vectors[movie_id] = self.model.embed(text)
        return self.vectors[movie_id]
```
* **Кэширование векторов:** вектор каждого фильма вычисляется моделью ровно один раз и сохраняется в словаре `self.vectors`. При повторных поисках расчет не повторяется, что делает поиск мгновенным!

---

## 4. Веб-слой: web.py (Flask)

Файл `web.py` содержит обработчики маршрутов:
* `@app.route('/')`: главная страница со списком фильмов и строкой поиска.
* `@app.route('/add', methods=['POST'])`: обработка формы добавления фильма.
* `@app.route('/api/search')`: REST API эндпоинт, возвращающий результаты поиска в формате JSON.

---

## 5. Точка сборки: run.py (Внедрение зависимостей)

```python
def build_service(search_strategy):
    repo = MovieRepository(Path('data/movies.db'))
    return CatalogService(repo, search_strategy)

def main():
    with load_embedder() as model:
        service = build_service(SemanticSearch(model))
        serve(service)
```
Все компоненты связываются воедино в одном месте. Чтобы сменить поиск по смыслу на поиск по словам, достаточно заменить `SemanticSearch(model)` на `KeywordSearch()`.

---

Вернуться к:
* [Уроку 5. Модель в веб-сервисе](05-movie-service.md)
* [Оглавлению второй ступени](README.md)
