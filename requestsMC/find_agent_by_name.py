import sys
import os
from configMC import headers
import requests


    # Добавляем родительскую директорию в путь
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


    # Функция для поиска контрагента по имени
def find_agent_by_name(agent_name):
    url = f"https://api.moysklad.ru/api/remap/1.2/entity/counterparty?filter=name={agent_name}"
        
    response = requests.get(url, headers=headers)
    #print(response)
        
    if response.status_code == 200:
        agents = response.json().get('rows', [])
        if agents:
                #print(f"Контрагент найден: {agents[0]['name']}")
            return agents[0]['meta']['href']  # Возвращаем ссылку на контрагента
        else:
            print(f"Контрагент с именем {agent_name} не найден.")
            return None
    else:
        print(f"Ошибка при поиске контрагента: {response.status_code}")
        return None