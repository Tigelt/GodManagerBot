import sys
import os
# Добавляем родительскую директорию в путь
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from configMC import headers
import requests


def get_organization_href():
    url = "https://api.moysklad.ru/api/remap/1.2/entity/organization"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Ошибка при получении организаций:", response.json())
        return None

    organizations = response.json().get("rows", [])
    
    for org in organizations:
        if "Shisha Da Nang" in org.get("name", ""):
            href = org["meta"]["href"]
            print(f"Найден хреф организации: {href}")
            return href

    print("Организация 'Shisha Da Nang' не найдена.")
    return None