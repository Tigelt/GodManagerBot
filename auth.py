from telethon import TelegramClient

API_ID = 14739654
API_HASH = '98c13db08224026ed85682c5ed3e1834'

client = TelegramClient('aimanager', API_ID, API_HASH)
client.start()  # тут он спросит номер, код и пароль 2FA
print("Готово, файл aimanager.session создан")