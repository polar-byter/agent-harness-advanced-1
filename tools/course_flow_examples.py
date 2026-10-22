"""Конкретные данные для схем уроков. Это сценарии объяснения, не записи запусков."""

ROOT = 'Agent Harness Workshop/Расширенный курс 1/Уроки/Материалы/'
STORIES = []


def transfer(action, source, before, destination, after, explanation, packet='данные', summary=None):
    result = dict(action=action, source=source, before=before, destination=destination,
                  after=after, explanation=explanation, packet=packet)
    if summary:
        result['summary'] = summary
    return result


def story(name, title, *scenes):
    STORIES.append(dict(path=ROOT + name + '.gif', title=title, scenes=list(scenes)))


story('lesson-01-ask', 'Как ask обращается к модели',
    transfer('demo.py вызывает ask', 'Вызов в demo.py',
             'ask(model, RULE, QUESTION,\n    schema=DAYS, max_tokens=32)',
             'Параметры ask', 'instruction = "Найди в пункте ..."\ntext = "Вопрос: Сколько дней ..."\nschema = {"days": integer}',
             'Модель уже загружена в память программы блоком with load_chat().', 'аргументы',
             'Правило, вопрос с пунктом и схема попадают в параметры ask.'),
    transfer('ask собирает сообщения', 'Параметры ask', 'instruction, text, schema',
             'messages и settings', '[system: правило + /no_think,\n user: вопрос и пункт]\nresponse_format: схема DAYS',
             'Схема превращается в грамматику: модель сможет написать только такой JSON.', 'сообщения'),
    transfer('Модель отвечает внутри программы', 'model.create_chat_completion', 'messages + settings\nHTTP-запроса нет',
             'response', '{"choices": [{"finish_reason": "stop",\n  "message": {"content": "{\\"days\\": 14}"}}]}',
             'Это обычный вызов функции Python: данные не покидают компьютер.', 'вызов'),
    transfer('ask возвращает словарь', 'clean_answer + json.loads', 'строка \'{"days": 14}\'',
             'Результат в demo.py', "data = {'days': 14}\ntype(data['days']) -> int",
             'clean_answer проверила finish_reason, json.loads превратила строку в словарь.', 'return'))

story('lesson-02-journal', 'Журнал из Excel превращается в разбор',
    transfer('Читаем журнал', 'data/journal.xlsx, лист "Журнал"', '03.10.2026 | Мама |\nСтащил со стола котлету...',
             'Список entries', "[{'date': '03.10.2026', 'author': 'Мама',\n  'text': 'Стащил со стола котлету...'}, ...]",
             'read_journal пропускает заголовок и строки без текста. Модель пока не участвует.', 'read_journal'),
    transfer('Разбираем одну запись', 'classify_entry(model, text)', 'text = "Стащил со стола котлету..."\nправило с пятью категориями',
             'Ответ ask со схемой', "{'category': 'кухня', 'severity': 1}",
             'enum в схеме разрешает только пять названий категорий.', 'ask + схема'),
    transfer('Собираем результаты', 'process_journal', 'запись + категория + серьёзность\nдля каждой из 12 записей',
             'results и подсчёт', "{'шум': 3, 'охота': 3, 'порча': 3,\n 'нежности': 2, 'кухня': 1}",
             'Записи разбираются по одной: так проще найти, на какой модель ошиблась.', '12 записей'),
    transfer('Сохраняем в Excel', 'results + сводка от модели', 'категории и текст сводки',
             'data/journal.xlsx', 'Новый лист "Разбор":\nзаписи, категории, серьёзность, сводка',
             'save_results пересоздаёт лист "Разбор", исходный лист журнала не меняется.', 'save_results'))

story('lesson-03-decisions', 'Как обращение попадает в очередь',
    transfer('Собираем вопрос', 'О-101 и вопрос queue', '"Хочу вернуть деньги за чайник,\n он не включается"\n6 вариантов из questions.json',
             'Текст запроса', 'Обращение клиента: Хочу вернуть...\nВопрос: Какая очередь...\n1. Возврат... 2. Претензия...',
             'Варианты пронумерованы: ответ модели - одна цифра.', 'prompt'),
    transfer('Модель оценивает первый токен', 'model.create_completion', 'max_tokens=1\nlogits_processor=[remember]',
             'Оценки токенов-номеров', '"1": 38.8  "2": 39.9  "3": 33.2\n"4": 30.1  "5": 27.6  "6": 33.8',
             'remember сохраняет оценки всех 151 936 токенов, нам нужны шесть.', 'оценки'),
    transfer('Оценки становятся вероятностями', 'softmax в option_probabilities', '[38.8, 39.9, 33.2, 30.1, 27.6, 33.8]',
             'Ответ ask_choice', "{'choice': 'претензии', 'confidence': 0.74,\n 'probabilities': {'возвраты': 0.26,\n  'претензии': 0.74, ...}}",
             'Ответ в том же виде, что у Jev.', 'ask_choice'),
    transfer('Решение принимает программа', 'route(answers, threshold=0.9)', "choice = 'претензии'\nconfidence = 0.74",
             'Решение', "'человеку'",
             '0.74 меньше порога 0.9: модель колеблется, обращение разберёт оператор.', 'route'))

story('lesson-04-photo', 'Фото из заявки и решение по нему',
    transfer('Готовим картинку', 'data/photos/phone.jpg', 'байты файла JPEG',
             'Строка data URI', '"data:image/jpeg;base64,/9j/4AAQ..."',
             'Картинка передаётся внутри сообщения текстом base64, файл никуда не загружается.', 'base64'),
    transfer('Собираем сообщение', 'Заявка А-1043', "item = 'смартфон'\nphoto = 'phone.jpg'",
             'Сообщение user', '[картинка: data:image/jpeg...,\n текст: "Заказанный товар: смартфон"]',
             'Содержимое сообщения - список из двух частей: картинки и текста.', 'messages'),
    transfer('Модель зрения отвечает по схеме', 'Qwen3-VL: проектор + языковая часть', 'картинка -> векторы\nтекст -> токены',
             'Ответ check_photo', "{'item': 'смартфон', 'same_item': True,\n 'damage_visible': True, 'comment': ...}",
             'Сначала модель называет предмет, потом сравнивает его с заказом.', 'JSON'),
    transfer('Программа выбирает маршрут', 'route_return(check)', 'same_item = True\ndamage_visible = True',
             'Решение', '"сотруднику: на фото видно повреждение"',
             'Решение строится по полям да/нет. Деньги возвращает сотрудник.', 'маршрут'))

story('lesson-05-service', 'Поиск по смыслу внутри веб-сервиса',
    transfer('Браузер присылает запрос', 'Адрес в браузере', '/?q=кино про хоккей',
             'web.py', "query = 'кино про хоккей'\nservice.find(query)",
             'Веб-слой читает параметр и передаёт его сервису.', 'HTTP'),
    transfer('Сервис берёт фильмы и стратегию', 'CatalogService.find', 'repository.list_all() -> 10 фильмов\nself.search -> SemanticSearch',
             'SemanticSearch.find', "query + 10 фильмов, top = 3",
             'Сервис не знает, какой поиск ему передали в run.py.', 'find'),
    transfer('Стратегия сравнивает векторы', 'SemanticSearch', 'vector(TASK + query)\nmovie_vector(movie) из self.vectors',
             'Пары (близость, фильм)', '(0.47, Легенда номер 17)\n(0.29, Москва слезам не верит) ...',
             'Векторы фильмов посчитаны один раз и лежат в словаре self.vectors.', 'cosine'),
    transfer('Страница со списком', 'Три лучших фильма', "['Легенда номер 17', ...]",
             'Браузер', 'index.html: карточки найденных фильмов',
             'Тот же результат /api/search отдаёт в виде JSON.', 'страница'))

story('lesson-06-speech', 'От голосового сообщения к карточке',
    transfer('Читаем звук', 'data/call.wav', '24,7 секунды, 16 000 Гц, моно, 16 бит',
             'audio', '395 280 чисел от -1 до 1\n[0.0, 0.0012, -0.0031, ...]',
             'read_wav проверяет формат и делит отсчёты на 32768.', 'read_wav'),
    transfer('Whisper распознаёт речь', 'model.transcribe(audio, language="ru")', '395 280 чисел',
             'Отрезки', "Segment(t0=744, t1=1164,\n  text=' Две недели назад...')",
             'Время отрезков - в сотых долях секунды.', 'Whisper'),
    transfer('Собираем строки с временем', 'Отрезок', 't0 = 744 -> 7 секунд\ntext.strip()',
             'lines', "'[00:07] Две недели назад я купила...'",
             'По отметке времени оператор быстро найдёт место в записи.', 'transcribe'),
    transfer('Qwen3 заполняет карточку', 'Строки расшифровки', '7 строк текста\nCALL_RULE + CALL_SCHEMA',
             'Карточка обращения', "{'name': 'Ольга Петрова', 'order': '4512',\n 'wish': 'вернуть деньги',\n 'callback': 'после 6 вечера'}",
             'Вторая модель получает только текст: ошибки первой переходят к ней.', 'ask + схема'))

story('lesson-07-bot', 'Путь сообщения через бота',
    transfer('Telegram отдаёт сообщение', 'Серверы Telegram', 'Маша: "Утащил со стола сосиску"',
             'bot.py, long polling', 'message.from_user.id = 5012...\nmessage.text = "Утащил со стола сосиску"',
             'Программа сама спрашивает Telegram о новых сообщениях.', 'getUpdates'),
    transfer('Проверяем белый список', 'message.from_user.id', '5012...',
             'data/allowed_users.txt', 'id есть в списке -> handle_text\nнет -> вежливый отказ',
             'Правило доступа записано в коде, сообщение в чате его не меняет.', 'id'),
    transfer('Разбираем и записываем', 'handle_text', 'classify_entry(model, text)',
             'data/journal.xlsx', "новая строка: дата, Маша, текст,\n'кухня', 2",
             'Тот же разбор, что в утилите из урока 2, и тот же журнал.', 'append_entry'),
    transfer('Отвечаем в чат', 'Строка ответа', '"Записал в журнал: кухня, серьёзность 2."',
             'Чат в Telegram', 'Ответ на сообщение Маши',
             'bot.reply_to отправляет ответ через Bot API.', 'reply_to'))
