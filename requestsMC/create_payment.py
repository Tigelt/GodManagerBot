from datetime import datetime
from telegram import Update
import requests
from configMC import headers

async def create_payment_for_order(order_href, update, context):
    url = "https://api.moysklad.ru/api/remap/1.2/entity/paymentin"

    order = context.user_data.get("last_order")
    if not order:
        await update.effective_chat.send_message("❌ Не найден заказ в контексте.")
        return

    organization_href = order["organization"]["meta"]["href"]
    agent_href = order["agent"]["meta"]["href"]

    data = {
        "operations": [{
            "meta": {
                "href": order_href,
                "type": "customerorder",
                "mediaType": "application/json"
            }
        }],
        #"moment": datetime.now().astimezone().isoformat(timespec="seconds"),  # всё же нужен, иначе 400
        "organization": {
            "meta": {
                "href": organization_href,
                "type": "organization",
                "mediaType": "application/json"
            }
        },
        "agent": {
            "meta": {
                "href": agent_href,
                "type": "counterparty",
                "mediaType": "application/json"
            }
        },
        "sum": order.get("sum", 0)  # или передавай фиксированное значение, если хочешь
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        await update.effective_chat.send_message("💰 Платёж создан.")
    else:
        await update.effective_chat.send_message(f"⚠️ Не удалось создать платёж: {response.text}")