import requests
import datetime
from requestsMC.find_agent_by_name import *
from requestsMC.get import *
from requestsMC.reserve_order import *
from requestsMC.modifications import *
from requestsMC.create_payment import *
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
    #order_data["project"] = {
    #    "meta": {
    #        "href": data['payment_method'],
    #        "type": "project",
    #        "mediaType": "application/json"
    #    }
    #}
    
    # Добавляю комментарий доставку
    order_data["description"] = str(data['delivery']/1000)



    #Достать организации
    #url = "https://api.moysklad.ru/api/remap/1.2/entity/organization"
    #response = requests.get(url, headers=headers)
    
    #if response.status_code == 200:
    #    orgs = response.json().get('rows', [])
    #    for org in orgs:
    #        print(f"Название: {org['name']}")
    #        print(f"Href: {org['meta']['href']}")
    #        print("------")
    #else:
    #    print(f"Ошибка {response.status_code}: {response.text}")

    #Достать ПРОЕКТ
    #url = "https://api.moysklad.ru/api/remap/1.2/entity/store"
    #response = requests.get(url, headers=headers)
     
    #if response.status_code == 200:
    #    orgs = response.json().get('rows', [])
    #    for org in orgs:
    #        print(f"Название: {org['name']}")
    #        print(f"Href: {org['meta']['href']}")
    #        print("------")
    #else:
    #    print(f"Ошибка {response.status_code}: {response.text}")


    # Добавляю позиции
    #order_data["positions"] = []
    #for item in data['items']:
    #        position = {
    #            "assortment": {
    #                "meta": {
    #                    "href": item['mod_href'],
    #                    "type": "variant",  # или "variant", если модификации — это варианты
    #                    "mediaType": "application/json"
    #                }
    #            },
    #            "quantity": item["quantity"],
    #            "price": item["price"]*100/item["quantity"]
    #        }
    #        order_data["positions"].append(position)


    # Отправка запроса на создание заказа
    url = "https://api.moysklad.ru/api/remap/1.2/entity/customerorder"
    json.dumps(order_data, ensure_ascii=False, indent=4)
    response = requests.post(url, json=order_data, headers=headers)


    print(response.text)
    
    if response.status_code == 200:
        #Cоздаю платеж
        #create_payment(response.json().get("meta", {}).get("href"), agent_href, total, payment_method)
        return response
    else:
        await update.message.reply_text(f"Не создался заказ")
        raise ValueError(f"Не создался заказ")
        return response
