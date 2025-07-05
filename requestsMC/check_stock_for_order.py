import sys
import os
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from configMC import headers

from urllib.parse import quote
import requests
from configMC import headers, IvanActual_href

def normalize_href(href: str) -> str:
    return href.split('?')[0] if href else ''

def check_stock_for_order(order_json):
    print("Проверяю остатки по заказу...")

    # 1. Получаем href склада из заказа
    store_meta = order_json.get('store', {}).get('meta', {})
    store_href = store_meta.get('href')
    if not store_href:
        print("Не удалось получить href склада из заказа")
        return False

    # Кодируем href для фильтра
    encoded_store_href = quote(store_href)

    # 2. Забираем список позиций из заказа
    positions = order_json.get('positions', {}).get('rows', [])
    if not positions:
        print("В заказе нет позиций")
        return False

    # 3. Получаем остатки по всем товарам
    stock_url = f"https://api.moysklad.ru/api/remap/1.2/report/stock/all?filter=store={encoded_store_href}"
    try:
        stock_response = requests.get(stock_url, headers=headers)
        if stock_response.status_code != 200:
            print(f"Ошибка при получении остатков: {stock_response.status_code}")
            print(stock_response.json())
            return False
    except Exception as e:
        print(f"Ошибка при обращении к API остатков: {e}")
        return False

    stock_data = stock_response.json().get('rows', [])

    # 4. Сопоставляем позиции заказа с остатками
    for pos in positions:
        assortment_meta = pos.get('assortment', {}).get('meta', {})
        product_href = assortment_meta.get('href')
        quantity = pos.get('quantity', 0)  # переводим из тысячных в целое число

        if not product_href:
            print("Позиция без href товара")
            return False

        found = False
        #print(product_href)
        for stock in stock_data:
            stock_href = stock.get('meta', {}).get('href')
            #print(stock_href)
            if normalize_href(stock_href) == product_href:
                available = stock.get('quantity', 0)
                print(f"{stock.get('name')}: доступно {available}, нужно {quantity}")
                if available < quantity:
                    print("Недостаточно остатков для списания")
                    return False
                found = True
                break

        if not found:
            print("Товар не найден в отчёте остатков")
            return False

    print("Всего хватает, можно отгружать")
    return True