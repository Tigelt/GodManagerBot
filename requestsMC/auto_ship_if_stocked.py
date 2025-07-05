import sys
import os
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from configMC import headers, IvanActual_href



def auto_ship_if_stocked(order_json):
    order_meta = order_json.get('meta', {}).get('href')
    positions = order_json.get('positions', {}).get('rows', [])
    #print(positions)
    demand_positions = []
    for pos in positions:
        demand_positions.append({
            "quantity": pos['quantity'],
            "assortment": pos['assortment']
        })
        print(pos)

    demand_data = {
        "customerOrder": {
            "meta": {
                "href": order_meta,
                "type": "customerorder",
                "mediaType": "application/json"
            }
        },
        "organization": order_json['organization'],
        "agent": order_json['agent'],
        "store": {
            "meta": {
                "href": IvanActual_href,
                "type": "store",
                "mediaType": "application/json"
            }
        },
        "positions": demand_positions
    }

    response = requests.post(
        "https://api.moysklad.ru/api/remap/1.2/entity/demand",
        headers=headers,
        json=demand_data
    )

    if response.status_code in [200, 201]:
        print("Отгрузка создана с позициями.")
        return response.json()
    else:
        print("Ошибка при создании отгрузки:")
        print(response.status_code)
        print(response.text)
        return None

