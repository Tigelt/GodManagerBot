import requests
from configMC import *

def create_payment(order_href, client_href, amount, payment_method):
    project_href = PROJECT_HREFS.get(payment_method)
    if not project_href:
        print(f"Проект не найден для способа оплаты: {payment_method}")
        return

    payload = {
        "organization": {
            "meta": {
                "href": organization_href,
                "type": "organization",
                "mediaType": "application/json"
            }
        },
        "agent": {
            "meta": {
                "href": client_href,
                "type": "counterparty",
                "mediaType": "application/json"
            }
        },
        "project": {
            "meta": {
                "href": project_href,
                "type": "project",
                "mediaType": "application/json"
            }
        },
        "operations": [
            {
                "meta": {
                    "href": order_href,
                    "type": "customerorder",
                    "mediaType": "application/json"
                }
            }
        ],
        "sum": amount*100
    }

    url = "https://api.moysklad.ru/api/remap/1.2/entity/paymentin"

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200 or response.status_code == 201:
        print("Платёж успешно создан!")
    else:
        print(f"Ошибка при создании платежа: {response.status_code}")
        print(response.text)