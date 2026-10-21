"""Подключение к Telegram: токен, обработчики команд и long polling."""
import os
from pathlib import Path

import telebot

from bot_logic import HELP, handle_text, read_allowed, summary_reply
from local_llm import load_chat

ROOT = Path(__file__).resolve().parent
JOURNAL = ROOT / 'data' / 'journal.xlsx'
ALLOWED = ROOT / 'data' / 'allowed_users.txt'
# Токен храним вне папки проекта: он не попадёт в архив, в репозиторий и на скриншот кода.
TOKEN_FILE = Path.home() / 'agent-secrets' / 'telegram_token.txt'


def read_token() -> str:
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    if not token and TOKEN_FILE.is_file():
        token = TOKEN_FILE.read_text(encoding='utf-8').strip()
    if not token:
        raise SystemExit(f'Нет токена бота. Сохраните его в файл {TOKEN_FILE}')
    return token


def main():
    allowed = read_allowed(ALLOWED)
    # threaded=False: сообщения обрабатываются по одному, модель не получает два запроса сразу.
    bot = telebot.TeleBot(read_token(), threaded=False)

    with load_chat() as model:
        @bot.message_handler(commands=['start', 'help'])
        def send_help(message):
            bot.reply_to(message, HELP)

        @bot.message_handler(commands=['id'])
        def send_id(message):
            bot.reply_to(message, f'Ваш id: {message.from_user.id}')

        @bot.message_handler(commands=['summary'])
        def send_summary(message):
            if message.from_user.id not in allowed:
                bot.reply_to(message, 'Сводка доступна только членам семьи.')
                return
            bot.send_chat_action(message.chat.id, 'typing')
            bot.reply_to(message, summary_reply(model, JOURNAL))

        @bot.message_handler(content_types=['text'])
        def add_entry(message):
            if message.from_user.id not in allowed:
                bot.reply_to(message, 'Я записываю проделки только от членов семьи. Ваш номер можно узнать командой /id.')
                return
            bot.send_chat_action(message.chat.id, 'typing')
            author = message.from_user.first_name or 'без имени'
            try:
                reply = handle_text(model, JOURNAL, author, message.text)
            except ValueError as error:
                reply = f'Не получилось разобрать запись: {error}'
            except PermissionError:
                reply = 'Не могу сохранить журнал: закройте journal.xlsx в Excel и пришлите запись ещё раз.'
            bot.reply_to(message, reply)

        print('Бот запущен, разрешённых пользователей:', len(allowed))
        print('Остановить: красный квадрат Stop в окне Run.')
        bot.infinity_polling()


if __name__ == '__main__':
    main()
