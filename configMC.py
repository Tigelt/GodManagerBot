# Заголовки запроса
headers = {
    'Authorization': 'Bearer 218308c31b56c829b5e21290eee3c0507e82dcaa',
    'Content-Type': 'application/json'
}

BOT_TOKEN = "7261041875:AAFOSkUuITFSHqwy19fJgLBSakke-n5zEJs"


organization_href = "https://api.moysklad.ru/api/remap/1.2/entity/organization/633ef336-39e0-11f0-0a80-065e00264b61"

IvanActual_href = "https://api.moysklad.ru/api/remap/1.2/entity/store/5b0a00a8-3b99-11f0-0a80-09fd0007829f"
IvanActual_id = "f46aa6b7-8ec1-11ef-0a80-00b7000fc6f3"

PROJECT_HREFS = {
    "Наличные": "https://api.moysklad.ru/api/remap/1.2/entity/project/fbc90130-a58e-11ef-0a80-0e2100006983",
    "Перевод": "https://api.moysklad.ru/api/remap/1.2/entity/project/ffd3fd9c-a58e-11ef-0a80-07aa00341c38",
    "Перевод Иван": "https://api.moysklad.ru/api/remap/1.2/entity/project/c86ef78d-d18f-11ef-0a80-064d002bd9e7"
}

order_data = {
        "organization": {
            "meta": {
                "href": organization_href, 
                "type": "organization",
                "mediaType": "application/json"
            }
        },
        "store": {
            "meta": {
            "href": IvanActual_href,
            "type": "store",
            "mediaType": "application/json"
            }
        },
        "reserve": True
}