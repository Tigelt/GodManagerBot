from telethon import TelegramClient

API_ID = 20732915
API_HASH = '76a13ac0c9479ad595d3a0f71be8e43d'

client = TelegramClient('aimanager', API_ID, API_HASH)
client.start()  # тут он спросит номер, код и пароль 2FA
print("Готово, файл aimanager.session создан")