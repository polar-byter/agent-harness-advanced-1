# Дополнительно: Как устроен журнал кота (app.py, journal_io.py, journal_ai.py)

> **Для кого этот материал:** В Уроке 2 вы дописали функцию `classify_entry`, а вокруг нее работал весь проект: чтение и запись Excel, подсчет статистики и графическое окно на Tkinter. 
> 
> Здесь мы подробно разберем все три ключевых модуля проекта, чтобы вы точно понимали, как они устроены строчка за строчкой.

---

## 1. Модуль journal_io.py: Работа с Excel через openpyxl

Файл `journal_io.py` полностью изолирует работу с таблицами Excel. Ни одна строка в нем не знает про нейросеть.

### Чтение журнала: функция read_journal
```python
def read_journal(path: Path) -> list[dict]:
    book = load_workbook(path, read_only=True)
    sheet = book.worksheets[0]
    entries = []
    for row in sheet.iter_rows(min_row=2, max_col=3, values_only=True):
        when, author, text = (as_text(value) for value in row)
        if text:
            entries.append({'date': when, 'author': author, 'text': text})
    book.close()
    return entries
```
* `load_workbook(path, read_only=True)`: флаг `read_only=True` ускоряет открытие больших файлов в разы и экономит память.
* `sheet.iter_rows(min_row=2, max_col=3, values_only=True)`:
  * `min_row=2`: пропускает строку заголовков и начинает сразу с данных.
  * `max_col=3`: считывает только первые три колонки (Дата, Автор, Текст).
  * `values_only=True`: возвращает сразу чистые значения ячеек, а не тяжелые объекты `Cell`.
* `as_text(value)`: вспомогательная функция, которая аккуратно преобразует даты Excel (`datetime.date`) в строку вида `'03.10.2026'`.

### Запись результатов: функция save_results
```python
def save_results(path: Path, results: list[dict], summary: str) -> None:
    book = load_workbook(path)
    if RESULT_SHEET in book.sheetnames:
        del book[RESULT_SHEET]
    sheet = book.create_sheet(RESULT_SHEET)
    sheet.append(HEADER + ['Категория', 'Серьёзность'])
    for item in results:
        sheet.append([item['date'], item['author'], item['text'], item['category'], item['severity']])
    sheet.append([])
    sheet.append(['Сводка для семьи', '', summary])
    for column, width in zip('ABCDE', (12, 14, 60, 12, 12)):
        sheet.column_dimensions[column].width = width
    book.save(path)
```
* Проверяет, есть ли уже лист "Разбор": если есть, удаляет старую версию, чтобы не плодить дубликаты.
* `sheet.append([...])`: быстро добавляет новую строку в конец таблицы.
* Настраивает ширину колонок (`sheet.column_dimensions[column].width = width`), чтобы текст не обрезался при открытии в Excel.

---

## 2. Модуль journal_ai.py: Промпты, классификация и сводка

### Структура промптов
```python
CATEGORIES = {
    'кухня': 'утащил или пытался утащить еду',
    'порча': 'испортил вещь: порвал, разбил, уронил, испачкал',
    'шум': 'мешал спать, громко орал, будил',
    'нежности': 'ласкался, мурлыкал, спал рядом',
    'охота': 'ловил насекомых, птиц, игрушки, гонялся за чем-то',
}
```
* `CLASSIFY_RULE` склеивает названия категорий и их описания через перенос строки. Описания служат для маленькой модели четкими ориентирами.
* `process_journal`: последовательно вызывает `classify_entry` для каждой строки и сообщает прогресс через коллбэк `on_progress(number, total)`.
* `count_categories`: использует стандартный `collections.Counter`, вычисляя количество инцидентов по категориям.
* `write_summary`: склеивает все события в один текст и просит модель написать шуточную семейную сводку без схемы JSON (в свободном стиле).

---

## 3. Модуль app.py: Графический интерфейс на Tkinter

Главная инженерная сложность десктопного интерфейса с локальным ИИ - **предотвращение зависания окна**.

### Архитектура неблокирующего интерфейса:
```python
def on_process_click():
    progress_queue = queue.Queue()
    
    def worker():
        with load_chat() as model:
            results = process_journal(model, entries, on_progress=progress_queue.put)
            summary = write_summary(model, results)
            progress_queue.put(('done', results, summary))
            
    threading.Thread(target=worker, daemon=True).start()
    window.after(100, check_queue)
```
1. `threading.Thread(...)`: запускает тяжелый инференс модели в отдельном потоке процессора. Основной поток Tkinter остается абсолютно свободным.
2. `queue.Queue()`: безопасный канал связи. Фоновый поток кладет туда сообщения о прогрессе (`progress_queue.put`).
3. `window.after(100, check_queue)`: главный поток окна раз в 100 мс заглядывает в очередь, достает свежие статусы и обновляет полосу прогресса и таблицу.

Благодаря этой связке окно свободно перетаскивается, кнопки нажимаются, а прогресс плавно отображается в реальном времени!

---

Вернуться к:
* [Уроку 2. Журнал проделок кота](02-cat-journal.md)
* [Оглавлению второй ступени](README.md)
