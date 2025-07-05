import sys
import os
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from configMC import headers

def get_order_with_positions(order_meta_href):
    url = f"{order_meta_href}?expand=positions"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка при получении заказа с позициями: {response.status_code}")
        print(response.text)
        return None