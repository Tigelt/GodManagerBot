def fetch_and_save_variants():
    url = "https://api.moysklad.ru/api/remap/1.2/entity/variant"
    offset = 0
    limit = 100
    all_variants = {}

    print("Загрузка модификаций...")

    while True:
        response = requests.get(f"{url}?limit={limit}&offset={offset}", headers=headers)
        if response.status_code != 200:
            print("Ошибка получения:", response.status_code)
            break

        data = response.json()
        rows = data.get('rows', [])
        if not rows:
            break

        for item in rows:
            name = item['name'].strip().lower()
            href = item['meta']['href']
            all_variants[name] = href
            #print(name)
        offset += limit

    with open("modifications.json", "w", encoding='utf-8') as f:
        json.dump(all_variants, f, ensure_ascii=False, indent=2)

    print(f"Сохранено модификаций: {len(all_variants)}")