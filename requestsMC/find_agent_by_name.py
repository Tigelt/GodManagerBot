import sys
import os
from configMC import headers
import requests
import json

    # Добавляем родительскую директорию в путь
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import os


# Функция для поиска контрагента по имени
# Возвращает href контрагента или None, если не найден
def find_agent_by_name(agent_name):
    json_file = "requestsMC/data/shisha/AgentNameHref.json"
    os.makedirs(os.path.dirname(json_file), exist_ok=True)


    with open(json_file, "r", encoding="utf-8") as f:
        agents = json.load(f)

    if not agents:
        save_all_agents_to_json(json_file)
    with open(json_file, "r", encoding="utf-8") as f:
        agents = json.load(f)
    # Проверим в текущем JSON
    #href = agents.get(agent_name)
    href = smart_get(agents, agent_name)
    
    if href:
        print(f"Контрагент {agent_name} найден в локальном JSON.")
        return href
    else:
        href = create_agent(agent_name)
        return href
    
def smart_get(agents, search_key):
    for name, href in agents.items():
        if search_key.lower() in name.lower():
            print(f"Нашел подходящего контрагента: {name}")
            return href
    print("Не найдено подходящего контрагента.")
    return None

# Функция для создания нового контрагента
# Если контрагента нет в базе, создаем его
# Возвращает href нового контрагента или None в случае ошибки
def create_agent(agent_name):
    url = "https://api.moysklad.ru/api/remap/1.2/entity/counterparty"
    json_file = "requestsMC/data/shisha/AgentNameHref.json"
    payload = {
        "name": agent_name,
        "tags": ["auto-created"],
        "legalTitle": "",    # можно оставить пустым
        "type": "individual" # это означает физлицо
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in (200, 201):
        data = response.json()
        href = data["meta"]["href"]
        print(f"Контрагент '{agent_name}' создан. Href: {href}")
        save_all_agents_to_json(json_file)
        return href
    else:
        print(f"Не удалось создать контрагента. Статус: {response.status_code}, ответ: {response.text}")
        return None

def save_all_agents_to_json(json_file):
    url = "https://api.moysklad.ru/api/remap/1.2/entity/counterparty"
    json_file = "requestsMC/data/shisha/AgentNameHref.json"
    os.makedirs(os.path.dirname(json_file), exist_ok=True)
    all_agents = {}
    next_url = url

    while next_url:
        response = requests.get(next_url, headers=headers)
        if response.status_code != 200:
            print(f"Ошибка при запросе: {response.status_code}")
            break

        data = response.json()
        for agent in data.get("rows", []):
            name = agent.get("name")
            href = agent.get("meta", {}).get("href")
            if name and href:
                all_agents[name] = href

        next_url = data.get("meta", {}).get("nextHref")
    #print(all_agents)
    # Сохраняем в JSON
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_agents, f, ensure_ascii=False, indent=2)

    print(f"Сохранено {len(all_agents)} контрагентов в {json_file}")