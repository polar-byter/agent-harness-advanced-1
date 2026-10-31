# Дополнительно: Как устроен Telegram-бот (bot.py и bot_logic.py)

> **Для кого этот материал:** В Уроке 7 мы собрали финальный проект курса - Telegram-бота, пополняющего Excel-журнал с помощью локальной модели Qwen3.
> 
> Здесь мы разберем устройство бота: безопасное чтение токена, декораторы команд, белый список пользователей и разделение логики.

---

## 1. Безопасность токена: функция read_token в bot.py

```python
def read_token() -> str:
    env_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if env_token:
        return env_token.strip()
    token_file = Path.home() / 'agent-secrets' / 'telegram_token.txt'
    if token_file.is_file():
        return token_file.read_text(encoding='utf-8').strip()
    raise FileNotFoundError(
        'Не найден токен бота. Задайте переменную TELEGRAM_BOT_TOKEN '
        f'или сохраните токен в файл {token_file}'
    )
```
* Токен никогда не хранится внутри репозитория или кода проекта.
* Функция сначала проверяет переменную окружения, а затем изолированный системный файл в домашней папке пользователя.

---

## 2. Белый список и авторизация: bot.py

```python
def load_allowed_users(path: Path) -> set[int]:
    if not path.is_file():
        return set()
    return {int(line.strip()) for line in path.read_text(encoding='utf-8').splitlines() 
            if line.strip().isdigit()}

def require_auth(handler):
    def wrapper(message):
        if message.from_user.id not in allowed_users:
            bot.reply_to(message, 'Доступ запрещен. Отправьте /id администратору бота.')
            return
        return handler(message)
    return wrapper
```
* Список пользователей загружается в быстрый `set[int]`.
* Любое входящее сообщение проверяется по числовому `from_user.id`.
* Посторонние пользователи не могут запустить инференс модели или записать данные в Excel.

---

## 3. Декораторы и обработчики сообщений

```python
@bot.message_handler(commands=['id'])
def send_id(message):
    bot.reply_to(message, f'Ваш id: {message.from_user.id}')

@bot.message_handler(commands=['summary'])
@require_auth
def send_summary(message):
    summary_text = handle_summary(model, journal_path)
    bot.reply_to(message, summary_text)

@bot.message_handler(content_types=['text'])
@require_auth
def on_text(message):
    bot.send_chat_action(message.chat.id, 'typing')
    reply = handle_text(model, journal_path, message.from_user.first_name, message.text)
    bot.reply_to(message, reply)
```
* `bot.send_chat_action(..., 'typing')`: включает статус *"печатает..."* в Telegram, пока локальная модель думает на процессоре.
* `threaded=False` в инициализации `TeleBot`: гарантирует, что запросы обрабатываются по очереди, исключая гонки потоков за модель.

---

## 4. Чистая логика бота: bot_logic.py

Файл `bot_logic.py` не импортирует библиотеку `telebot`. Он принимает чистые строки и возвращает готовый ответ.
Благодаря этому логику работы бота можно протестировать через `demo.py` или юнит-тесты без подключения к серверам Telegram!

---

Вернуться к:
* [Уроку 7. Telegram-бот на локальной модели](07-telegram-bot.md)
* [Оглавлению второй ступени](README.md)
