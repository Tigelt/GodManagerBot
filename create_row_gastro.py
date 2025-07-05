import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def create_row_gastro(data, update):
    # Настройка доступа
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("shisha-464813-f958df479144.json", scope)
    client = gspread.authorize(creds)
    sheetS = client.open_by_key("10u_ZTPARIIH6Sow7iDxasJFFerfSX2sD36mF5krMBW8")
    sheet = sheetS.worksheet("GastroHeaven")

	# Подготовим данные
    now = datetime.now()
    date_str = now.strftime("%d.%m")
    time_str = now.strftime("%H:%M")
    date_now = f"{date_str}\n\n{time_str}"

    client_name = data['Клиент']
    delivery = data['Доставка']
    
    cash = ''
    transfer = ''
    print(data['Способ оплаты'].lower())
    if 'наличные' in data['Способ оплаты'].lower():
        cash = data['Сумма']
    elif 'перевод' in data['Способ оплаты'].lower():
        transfer = data['Сумма']
    else:
        cash = data['Сумма']  

    # Соберём заказ в текст
    order_text = "\n".join([f"{item['name']} x{item['quantity']}" for item in data['Заказ']])

    # Собираем строку для таблицы
    row = [date_now, client_name, delivery, cash, transfer]

    # Пишем
    sheet.append_row(row, value_input_option="USER_ENTERED")
    print("Записал строку!")