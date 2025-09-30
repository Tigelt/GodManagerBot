import os
import sys
from telethon import TelegramClient
from dotenv import load_dotenv

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')

client = TelegramClient('botAccount.session', api_id, api_hash)
client.start()  # тут он спросит номер, код и пароль 2FA
print(f"Готово, файл botAccount.session создан")
