import requests
from requestsMC.find_agent_by_name import *
from requestsMC.get_positions import get_positions
from configMC import order_data, PROJECT_HREFS


# Функция для создания заказа
async def create_order(data, update):

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
    with open("requestsMC/data/shisha/ProjectNameHref.json", "r", encoding="utf-8") as f:
        project_hrefs = json.load(f)

    href = project_hrefs.get(data['payment'].lower(), None)
    
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
    
    if response.status_code == 200:
        await update.message.reply_text(f"✅ Заказ создан в МС")
        print("✅ Заказ создан в МС")
        return response
    else:
        await update.message.reply_text(f"Не создался заказ")
        raise ValueError(f"Не создался заказ")
        return response
