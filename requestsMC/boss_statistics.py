import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from configMC import headers
import requests
import calendar
import json

def get_stats_for_sheet(sheet, today, week_start, week_end):
    """Считает статистику по одному листу"""
    values = sheet.get_all_values()

    orders_today = []
    orders_week = []
    revenue_today = 0
    revenue_week = 0

    for row in values[1:]:  # пропускаем заголовок
        if not row or not row[0].strip():
            continue

        try:
            date_part = row[0].strip().split("\n")[0]
            order_date = datetime.strptime(date_part, "%d.%m").date()
            order_date = order_date.replace(year=today.year)
        except ValueError:
            continue

        # Сумма заказа = D + E
        try:
            cash = int(row[4]) if len(row) > 4 and row[4].strip().isdigit() else 0
        except:
            cash = 0
        try:
            transfer = int(row[5]) if len(row) > 5 and row[5].strip().isdigit() else 0
        except:
            transfer = 0
        try:
            transferIlya = int(row[6]) if len(row) > 6 and row[6].strip().isdigit() else 0
        except:
            transferIlya = 0

        order_sum = cash + transfer + transferIlya

        if order_date == today:
            orders_today.append(row)
            revenue_today += order_sum

        # Календарная неделя
        if week_start <= order_date <= week_end:
            orders_week.append(row)
            revenue_week += order_sum
            

    return {
        "orders_today": len(orders_today),
        "revenue_today": revenue_today,
        "orders_week": len(orders_week),
        "revenue_week": revenue_week
    }
    
async def boss_statistics(update, context):
    # Авторизация
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("shisha-464813-781e939944ae.json", scope)
    client = gspread.authorize(creds)

    # Даты
    today = datetime.today().date()
    week_start = today - timedelta(days=today.weekday())  # понедельник
    week_end = week_start + timedelta(days=6)              # воскресенье

    # Статистика по Shisha
    shisha_sheet = client.open_by_key("10u_ZTPARIIH6Sow7iDxasJFFerfSX2sD36mF5krMBW8").worksheet("Shisha")
    shisha_stats = get_stats_for_sheet(shisha_sheet, today, week_start, week_end)

    # Статистика по GastroHeaven
    gastro_sheet = client.open_by_key("10u_ZTPARIIH6Sow7iDxasJFFerfSX2sD36mF5krMBW8").worksheet("GastroHeaven")
    gastro_stats = get_stats_for_sheet(gastro_sheet, today, week_start, week_end)

    # Общая статистика
    total_today = shisha_stats["revenue_today"] + gastro_stats["revenue_today"]
    total_week = shisha_stats["revenue_week"] + gastro_stats["revenue_week"]

    report = (
    "📊 Статистика заказов\n"
    "──────────────────\n"
    f"Оборот сегодня:        {total_today}\n"
    f"Оборот за неделю:      {total_week}\n"
    "──────────────────\n\n"

    "🍃 ShiSha\n"
    f"• Заказов сегодня:      {shisha_stats['orders_today']}\n"
    f"• Выручка сегодня:      {shisha_stats['revenue_today']}\n"
    f"• Заказов за неделю:    {shisha_stats['orders_week']}\n"
    f"• Выручка за неделю:    {shisha_stats['revenue_week']}\n\n"

    "🍽 GastroHeaven\n"
    f"• Заказов сегодня:      {gastro_stats['orders_today']}\n"
    f"• Выручка сегодня:      {gastro_stats['revenue_today']}\n"
    f"• Заказов за неделю:    {gastro_stats['orders_week']}\n"
    f"• Выручка за неделю:    {gastro_stats['revenue_week']}\n"
)

    await update.message.reply_text(report)
    


async def money_month(update, context):
    url = "https://api.moysklad.ru/api/remap/1.2/entity/demand"
    params = {
        "limit": 1,
        "order": "moment,desc"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    rows = data.get('rows', [])
    if not rows:
        msg = "Нет данных по последним отгрузкам."
        print(msg)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
        return

    last_demand = rows[0]
    
    #print(json.dumps(last_demand.get('positions', {}), indent=2, ensure_ascii=False))
    positions_href = last_demand["positions"]["meta"]["href"]
    resp = requests.get(positions_href, headers=headers)
    resp.raise_for_status()
    positions_data = resp.json()

    for pos in positions_data.get("rows", []):
        assortment = pos.get("assortment", {})
        product_href = assortment.get("meta", {}).get("href")
        if product_href:
            prod_resp = requests.get(product_href, headers=headers)
            prod_resp.raise_for_status()
            prod_data = prod_resp.json()
        
            # теперь печатаем JSON самого товара
            print(json.dumps(prod_data, ensure_ascii=False, indent=2))
    
    positions_block = last_demand.get('positions', {})
    positions = []
    if isinstance(positions_block, dict) and 'rows' in positions_block:
        positions = positions_block.get('rows', [])

    product_names = []
    for pos in positions:
        assortment = pos.get('assortment', {})
        product_href = assortment.get('meta', {}).get('href')
        if product_href:
            prod_resp = requests.get(product_href, headers=headers)
            prod_resp.raise_for_status()
            prod_data = prod_resp.json()
            product_name = prod_data.get('name', 'Без названия')
            product_names.append(product_name)
            print(product_name)

    if product_names:
        msg = "\n".join(product_names)
    else:
        msg = "Позиции не найдены."

    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)