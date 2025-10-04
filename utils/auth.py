import os
import sys
from telethon import TelegramClient
from dotenv import load_dotenv

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

api_id = int(os.getenv('TELEGRAM_API_ID', '0'))
api_hash = os.getenv('TELEGRAM_API_HASH', '')

session_file = 'botAccount.session'

# Проверяем существование файла сессии
if os.path.exists(session_file):
    print(f"✅ Файл {session_file} уже существует, ничего не делаем")
else:
    print(f"🔧 Файл {session_file} не найден, создаем...")
    client = TelegramClient(session_file, api_id, api_hash)
    client.start()  # тут он спросит номер, код и пароль 2FA
    print(f"✅ Готово, файл {session_file} создан")
