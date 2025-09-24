import requests
from requestsMC import change_state
from requestsMC.change_state import change_order_state, get_order_states
from requestsMC.create_demand_for_order import create_demand_for_order
from requestsMC.create_payment import create_payment_for_order
from requestsMC.find_agent_by_name import *
from requestsMC.get_positions import get_positions
from configMC import order_data, PROJECT_HREFS, organization_href, headers, dostavlenState_href
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler




# Функция для создания заказа
async def create_order(data, update, context):

    # Указываю контрагента
    agent_href = find_agent_by_name(data['username'])
    if not agent_href:
        await update.message.reply_text(f"Не нашел клиента {data['username']}")
    order_data["agent"] = {
        "meta": {
            "href": agent_href,
            "type": "counterparty",
            "mediaType": "application/json"
        }
    }

    # Указываю проект
    href = PROJECT_HREFS.get(data['payment'].lower(), None)
    order_data["project"] = {
       "meta": {
           "href": href,
           "type": "project",
           "mediaType": "application/json"
       }
    }
    
    # Добавляю комментарий доставку
    order_data["description"] = str(data['delivery'])

    order_data["state"] = {
        "meta": {
            "href": "https://api.moysklad.ru/api/remap/1.2/entity/customerorder/metadata/states/636b5ae8-39e0-11f0-0a80-065e00264b95",
            "type": "state",
            "mediaType": "application/json"
        }
    }   

    # Добавляю позиции
    order_data["positions"] = get_positions(data['items'], update)

    # Отправка запроса на создание заказа
    url = "https://api.moysklad.ru/api/remap/1.2/entity/customerorder"
    json.dumps(order_data, ensure_ascii=False, indent=4)
    response = requests.post(url, json=order_data, headers=headers)
    #print(response.text)
    #await get_order_states()
    
    if response.status_code == 200:
        await update.message.reply_text(f"✅ Заказ создан в МС")
        print("✅ Заказ создан в МС")
        order= response.json()
        #print(order)
        await check_order(order.get("meta", {}).get("href"), update, data)
        # Сохраняем response
        context.user_data["last_order"] = response.json()

        # Потом, в callback handler'е:
        order = context.user_data.get("last_order")
        return response
    else:
        await update.message.reply_text(f"Не создался заказ")
        raise ValueError(f"Не создался заказ")
        return response

async def check_order(href, update, data):
    positions_url = href + "/positions"
    order_sum = 0

    positions_response = requests.get(positions_url, headers=headers)
    positions = positions_response.json().get("rows", [])

    result_lines = []

    for pos in positions:
        quantity = pos.get("quantity", 0)
        price = pos.get("price", 0) / 100  # цена в копейках
        total = quantity * price
        order_sum += total

        # Получаем ссылку на вариант или товар
        product_href = pos.get("assortment", {}).get("meta", {}).get("href")
        product_response = requests.get(product_href, headers=headers)
        product_data = product_response.json()
        name = product_data.get("name", "❓Без названия")

        # Формируем строку
        line = f"• {name} — x{quantity} {total:.0f} VND"
        result_lines.append(line)

    full_message = f"🧾 {order_sum}\n" + "\n".join(result_lines)
    #print(full_message)

    # Если хочешь отправить это в Телеграм
    await ask_order_confirmation(update, full_message, data)

    return full_message



async def ask_order_confirmation(update, product_summary, data):
    overheads = 0
    if abs((data['total'] - data['summa'] - data['delivery'])) == data['delivery']:
        overheads = data['delivery']
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=f"confirm_order:{overheads}"),
            InlineKeyboardButton("❌ Нет", callback_data="cancel_order"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🧾 Подтвердить заказ?\n\nНакладные расходы: {overheads}\n\n{product_summary}",
        reply_markup=reply_markup
    )
   
   
   
    
async def handle_order_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")
    action = data[0]  # confirm_order или cancel_order
    overheads = int(data[1]) if len(data) > 1 else 0

    if action == "confirm_order":
        await query.edit_message_text("✅ Заказ подтверждён. Создаю платёж...")

        # Достаём заказ, сохранённый ранее
        order = context.user_data.get("last_order")
        if not order:
            await query.edit_message_text("❗ Ошибка: заказ не найден в контексте.")
            return

        href = order.get("meta", {}).get("href")
        if not href:
            await query.edit_message_text("❗ Ошибка: у заказа нет ссылки.")
            return

        # Тут вызываем создание платежа
        
        await create_payment_for_order(href, update, context)
        demand = await create_demand_for_order(href, update, context, overheads)
        if demand.status_code == 200:
            await change_order_state(href, dostavlenState_href)

    elif query.data == "cancel_order":
        await query.edit_message_text("❌ Заказ отменён.")

