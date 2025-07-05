import requests


url = "https://api.moysklad.ru/api/remap/1.2/entity/store"
headers = {
    "Authorization": f"Bearer 2c6fc7a5ba9ef8ee55ea74ab7b501c4e416b2a0d",
    "Accept-Encoding": "gzip",
    'Content-Type': 'application/json'
}

#response = requests.get(url, headers=headers)

response = requests.get('https://api.moysklad.ru/api/remap/1.2/entity/customerorder', headers=headers)

print('Status:', response.status_code)
print('Response:', response.text)


products = get_all_variants()
    positions = []
    for item in items:
        product_name = item['name'].lower()
        product_href = products.get(product_name)
        if product_href:
            position = {
                "quantity": item['quantity'],
                "price": item['price'] * 1000,  # цена в копейках
                "assortment": {
                    "meta": {
                    "href": product_href,
                    "type": "product",
                    "mediaType": "application/json"
                    }
                }
            }
            positions.append(position)
        else:
            print(f"Товар '{item['name']}' не найден в МойСклад.")
    