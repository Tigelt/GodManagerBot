from datetime import datetime
import requests
from telegram import Update
from configMC import headers

async def create_demand_for_order(order_href, update, context, overheads):
    url = "https://api.moysklad.ru/api/remap/1.2/entity/demand"

    order = context.user_data.get("last_order")
    if not order:
        await update.effective_chat.send_message("❌ Не найден заказ в контексте.")
        return

    organization_href = order["organization"]["meta"]["href"]
    agent_href = order["agent"]["meta"]["href"]
    store_href = order["store"]["meta"]["href"]
    
    positions_url = order["positions"]["meta"]["href"]
    response = requests.get(positions_url, headers=headers)
    rows = response.json()["rows"]

    demand_positions = []
    for item in rows:
        demand_positions.append({
            "assortment": item["assortment"],
            "quantity": item["quantity"],
            "price": item["price"]
        })
        
    data = {
        #"moment": datetime.now().astimezone().isoformat(timespec="seconds"),
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
        "store": {
            "meta": {
                "href": store_href,
                "type": "store",
                "mediaType": "application/json"
            }
        },
        "positions": demand_positions,
        "customerOrder": {
            "meta": {
                "href": order_href,
                "type": "customerorder",
                "mediaType": "application/json"
            }
        },
        "description": "🚚 Доставка в накладных расходах" if overheads > 0 else "💰 Доставка оплачена клиентом"
    }

    if overheads > 0:
        data["overhead"] = {
            "sum": int(overheads)*100000,
            "distribution": "price"
        }

    response = requests.post(url, headers=headers, json=data)
    #import json
    #print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    

    if response.status_code == 200:
        await update.effective_chat.send_message("📦 Отгрузка создана.")
        return response
    else:
        
        await update.effective_chat.send_message(f"⚠️ Не удалось создать отгрузку: {response.text}")
        return response