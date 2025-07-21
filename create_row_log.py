import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from gspread_formatting import CellFormat, Color, format_cell_range


async def create_row_log(data, update):
    # Настройка доступа
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("shisha-464813-781e939944ae.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key("10u_ZTPARIIH6Sow7iDxasJFFerfSX2sD36mF5krMBW8").sheet1

	# Подготовим данные
    org = update.message.from_user.username
    now = datetime.utcnow() + timedelta(hours=7)
    date_str = now.strftime("%d.%m")
    time_str = now.strftime("%H:%M")
    date_now = f"{date_str}\n\n{time_str}"
    address = data['address']
    number = data['number']
    client_name = data['username'].lstrip('@')  # удаляет @ в начале
    client_link = f"https://t.me/{client_name}"
    comment = data['comment']
    cash = ''
    transfer = ''
 
    if 'наличные' in data['payment'].lower():
        cash = data['summa']
    elif 'иванкр' in data['payment'].lower():
        transfer = data['summa']
    elif 'перевод' in data['payment'].lower():
        transfer = data['summa']
    else:
        cash = data['summa']
 ###       
    user = update.message.from_user.username
    color = (
    "blue" if "ShishaDanang" in user else
    "yellow" if "Gastroheaven" in user else
    "white"
    )

# Соберём заказ
    order_text = "\n".join([f"{item['name']} x{item['quantity']}" for item in data['items']])
    row = [date_now, client_link, address, number, comment, cash, transfer, order_text]

    try:
        sheet.insert_row(row, index=2)

        # Красим вторую строку (теперь именно она вставлена)
        fmt = CellFormat(backgroundColor={
            "blue":   Color(0.678, 0.847, 0.902),
            "yellow": Color(1, 1, 0.6),
            "white":  Color(1, 1, 1)
        }[color])
        format_cell_range(sheet, "A2:H2", fmt)

        print("✅ Строка вставлена во вторую строку и покрашена")
        await update.message.reply_text("✅ Строка вставлена во вторую строку и покрашена")

    except Exception as e:
        print("❌ Ошибка при вставке строки:", e)
        await update.message.reply_text(f"❌ Ошибка: {e}")