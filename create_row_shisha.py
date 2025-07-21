import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

async def create_row_shisha(data, update):
    # Настройка доступа
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("shisha-464813-781e939944ae.json", scope)
    client = gspread.authorize(creds)
    sheetS = client.open_by_key("10u_ZTPARIIH6Sow7iDxasJFFerfSX2sD36mF5krMBW8")
    sheet = sheetS.worksheet("Shisha")

	# Подготовим данные
    now = datetime.utcnow() + timedelta(hours=7)
    date_str = now.strftime("%d.%m")
    time_str = now.strftime("%H:%M")
    date_now = f"{date_str}\n\n{time_str}"
    username = data['username'].lstrip('@')  # удаляет @ в начале
    client_link = f"https://t.me/{username}"
    delivery = data['delivery']
    delivery2 = ''
    cash = ''
    transfer = ''
    if 'наличные' in data['payment'].lower():
        cash = data['summa']
    elif 'иванкр' in data['payment'].lower():
        transfer = data['summa']
    elif 'перевод' in data['payment'].lower():
        cash = 0
    else:
        cash = data['summa']

    # Соберём заказ в текст
    order_text = "\n".join([f"{item['name']} x{item['quantity']}" for item in data['items']])
    # Собираем строку для таблицы
    row = [date_now, client_link, delivery, cash, transfer]
    try:
        #sheet.append_row(row, value_input_option="USER_ENTERED")
        sheet.insert_row(row, index=4, value_input_option="RAW")
        print("✅ Строка вставлена в ShiSha")
        await update.message.reply_text(f"✅ Строка вставлена в ShiSha")
    except Exception as e:
        print("❌ Ошибка при вставке в ShiSha строки:", e)
        await update.message.reply_text(f"❌ Ошибка при вставке в ShiSha строки: {e}")
