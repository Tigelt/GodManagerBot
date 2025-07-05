import sys
import os
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from configMC import headers

def reserve_order(order_meta_href):
    print("Пробую зарезервировать заказ...")
    reserve_data = {
        "reserved": True
    }
    response = requests.put(order_meta_href, headers=headers, json=reserve_data)
    
    if response.status_code == 200:
        print("Успешно зарезервировано!")
    else:
        print(f"Ошибка при резервировании: {response.status_code}")
        print(response.json())