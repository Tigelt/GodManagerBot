from configMC import headers
import requests
import json


async def get_order_states(href):
    url = "https://api.moysklad.ru/api/remap/1.2/entity/customerorder/metadata"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    states = data.get("states", [])
    for s in states:
        name = s.get("name")
        href = s.get("meta", {}).get("href")
        print(f"{name} — {href}")

    return states

async def change_order_state(order_href: str, state_href: str):
    payload = {
        "state": {
            "meta": {
                "href": state_href,
                "type": "state",
                "mediaType": "application/json"
            }
        }
    }
    response = requests.put(order_href, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()