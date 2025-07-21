
import json
import os
from urllib import request
from configMC import headers
import requests


def get_positions(data, update):
    order_data = []
    json_file = "requestsMC/data/shisha/ItemNameHref.json"
    os.makedirs(os.path.dirname(json_file), exist_ok=True)


    with open(json_file, "r", encoding="utf-8") as f:
        item = json.load(f)

    if not item:
        save_all_item_to_json(json_file)
    with open(json_file, "r", encoding="utf-8") as f:
        itemJSON = json.load(f)

    itemHref = None

    #print(data)
    for item in data:
            itemHref = smart_get(item['name'], itemJSON)
            position = {
               "assortment": {
                   "meta": {
                       "href": itemHref,
                       "type": "variant", 
                       "mediaType": "application/json"
                   }
               },
               "quantity": item["quantity"],
               "price": item["price"]/item["quantity"]*100000
           }
            if itemHref:
                order_data.append(position)
    return order_data






def save_all_item_to_json(json_file):
    url = "https://api.moysklad.ru/api/remap/1.2/entity/variant"
    json_file = "requestsMC/data/shisha/ItemNameHref.json"
    #os.makedirs(os.path.dirname(json_file), exist_ok=True)
    all_items = {}
    next_url = url

    while next_url:
        response = requests.get(next_url, headers=headers)
        if response.status_code != 200:
            print(f"Ошибка при запросе: {response.status_code}")
            break

        data = response.json()
        for item in data.get("rows", []):
            name = item.get("name")
            href = item.get("meta", {}).get("href")
            if name and href:
                all_items[name] = href

        next_url = data.get("meta", {}).get("nextHref")
    #print(all_items)
    # Сохраняем в JSON
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    print(f"Сохранено {len(all_items)} товаров в {json_file}")

# def smart_get(item_name, items_json):
#     search_words = item_name.strip().lower().split()
#     for name, href in items_json.items():
#         name_words = name.lower().split()
#         #print(f"Проверка товара: {name} на наличие слов: {search_words}")
#         if all(any(word in name_part for name_part in name_words) for word in search_words):
#             #print(f"Нашел подходящий товар: {name}")
#             return href
#     print(f"Не найдено подходящего товара для: {item_name}")
#     return None

def smart_get(item_name, items_json):
   
    search_words = item_name.strip().lower().split()
    #print(f"Поисковые слова: {search_words}")
    for name, href in items_json.items():
        full_name = name.lower()
        #print(f"Сравниваю с: {full_name}")
        if all(word in full_name for word in search_words):
            print(f"Нашел подходящий товар: {name}")
            return href
    print(f"Не найдено подходящего товара для: {item_name}")
    return None

