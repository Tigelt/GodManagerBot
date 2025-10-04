"""
Сервис для работы с API Мой Склад
"""

import aiohttp
import json
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class MoySkladAPI:
    """API клиент для Мой Склад"""
    
    def __init__(self, token: str, config: dict = None):
        self.token = token
        self.config = config or {}
        self.base_url = "https://api.moysklad.ru/api/remap/1.2/"
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    async def create_order(self, order_data: Dict) -> Dict:
        """Создание заказа"""
        url = f"{self.base_url}entity/customerorder"
        
        # Получаем agent_href динамически
        agent_href = await self.find_agent_by_name(order_data.get('username', ''))
        if not agent_href:
            raise Exception(f"Не найден клиент {order_data.get('username', '')}")
        
        # Добавляем обязательные поля для Мой Склад
        order_data['agent'] = {
            "meta": {
                "href": agent_href,
                "type": "counterparty",
                "mediaType": "application/json"
            }
        }
        order_data['organization'] = {
            "meta": {
                "href": self.config.get('organization_href'),
                "type": "organization", 
                "mediaType": "application/json"
            }
        }
        order_data['store'] = {
            "meta": {
                "href": self.config.get('store_href'),
                "type": "store",
                "mediaType": "application/json"
            }
        }
        
        # Добавляем проект (способ оплаты)
        payment = order_data.get('payment_method', '').lower()
        project_href = self.config.get('project_hrefs', {}).get(payment)
        if project_href:
            order_data['project'] = {
                "meta": {
                    "href": project_href,
                    "type": "project",
                    "mediaType": "application/json"
                }
            }
        
        # Добавляем комментарий (доставка)
        delivery = order_data.get('delivery_cost', '')
        order_data['description'] = str(delivery)
        
        # Добавляем позиции товаров
        positions = await self._get_positions(order_data.get('items', []))
        if positions:
            order_data['positions'] = positions
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=order_data, headers=self.headers) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Заказ создан в МС")
                    logger.info("✅ Заказ создан в Мой Склад")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка создания заказа: {error_text}")
                    raise Exception(f"Ошибка создания заказа: {error_text}")
    
    async def get_order_positions(self, order_href: str) -> Dict:
        """Получение позиций заказа в формате {название_товара: {quantity, price}}"""
        url = f"{order_href}/positions"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    positions = data.get('rows', [])
                    
                    # Формируем словарь {название: {quantity, price}}
                    products_dict = {}
                    for position in positions:
                        # Получаем информацию о товаре по его href
                        product_href = position.get('assortment', {}).get('meta', {}).get('href')
                        if product_href:
                            product_info = await self._get_product_info(session, product_href)
                            product_name = product_info.get('name', 'Товар')
                        else:
                            product_name = 'Товар'
                        
                        # Добавляем в словарь
                        products_dict[product_name] = {
                            'quantity': position.get('quantity', 0),
                            'price': (position.get('price', 0) / 100)*position.get('quantity', 0)  # Конвертируем в рубли
                        }
                    
                    return products_dict
                else:
                    logger.error(f"❌ Ошибка получения позиций: {response.status}")
                    return {}
    
    async def _get_product_info(self, session, product_href: str) -> Dict:
        """Получение информации о товаре"""
        try:
            async with session.get(product_href, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {}
        except Exception as e:
            logger.error(f"❌ Ошибка получения товара: {e}")
            return {}
    
    async def get_order_by_href(self, order_href: str) -> Optional[Dict]:
        """Получение заказа по href"""
        async with aiohttp.ClientSession() as session:
            async with session.get(order_href, headers=self.headers) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Заказ получен: {order_href}")
                    return result
                else:
                    logger.error(f"❌ Ошибка получения заказа: {response.status}")
                    return None
    
    async def get_agent_by_href(self, agent_href: str) -> str:
        """Получение полного имени клиента по href"""
        async with aiohttp.ClientSession() as session:
            async with session.get(agent_href, headers=self.headers) as response:
                if response.status == 200:
                    result = await response.json()
                    # Получаем полное имя клиента
                    name = result.get('name', 'Не указано')
                    
                    return name
                else:
                    logger.error(f"❌ Ошибка получения агента: {response.status}")
                    return 'Не указано'
    
    async def create_demand(self, order_href: str, overheads: int = 0) -> Dict:
        """Создание отгрузки"""
        url = f"{self.base_url}entity/demand"
        
        # Получаем заказ по href
        order = await self.get_order_by_href(order_href)
        if not order:
            raise Exception("Заказ не найден")
        
        # Получаем позиции заказа
        positions_url = order["positions"]["meta"]["href"]
        
        async with aiohttp.ClientSession() as session:
            positions_response = await session.get(positions_url, headers=self.headers)
            positions_data = await positions_response.json()
            positions_rows = positions_data.get("rows", [])
            
            # Формируем позиции для отгрузки
            demand_positions = []
            for item in positions_rows:
                demand_positions.append({
                    "assortment": item["assortment"],
                    "quantity": item["quantity"],
                    "price": item["price"]
                })
            
            # Формируем данные для отгрузки
            demand_data = {
                "organization": order["organization"],
                "agent": order["agent"],
                "store": order["store"],
                "positions": demand_positions,
                "customerOrder": {
                    "meta": {
                        "href": order_href,
                        "type": "customerorder",
                        "mediaType": "application/json"
                    }
                },
                "description": "🚚 Доставка в накладных расходах" if overheads > 0 else "💰 Доставка оплачена клиентом"
            }
            
            # Добавляем накладные расходы если нужно
            if overheads > 0:
                demand_data["overhead"] = {
                    "sum": int(overheads) * 100000,  # В копейках
                    "distribution": "price"
                }
            
            async with session.post(url, json=demand_data, headers=self.headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка создания отгрузки: {error_text}")
                    raise Exception(f"Ошибка создания отгрузки: {error_text}")
    
    async def create_payment(self, order_href: str) -> Dict:
        """Создание платежа"""
        url = f"{self.base_url}entity/paymentin"
        
        # Получаем заказ по href
        order = await self.get_order_by_href(order_href)
        if not order:
            raise Exception("Заказ не найден")
        
        # Формируем данные для платежа (только нужные поля)
        payment_data = {
            "operations": [{
                "meta": {
                    "href": order_href,
                    "type": "customerorder",
                    "mediaType": "application/json"
                }
            }],
            "organization": {
                "meta": {
                    "href": self.config.get('organization_href'),
                    "type": "organization",
                    "mediaType": "application/json"
                }
            },
            "agent": {
                "meta": {
                    "href": order["agent"]["meta"]["href"],
                    "type": "counterparty",
                    "mediaType": "application/json"
                }
            },
            "sum": order.get("sum", 0)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payment_data, headers=self.headers) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ Платеж создан")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка создания платежа: {error_text}")
                    raise Exception(f"Ошибка создания платежа: {error_text}")
    
    async def change_order_state(self, order_href: str, state_href: str) -> Dict:
        """Изменение состояния заказа"""
        url = order_href
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json={"state": {"meta": {"href": state_href, "type": "state", "mediaType": "application/json"}}}, headers=self.headers) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ Состояние заказа изменено")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка изменения состояния: {error_text}")
                    raise Exception(f"Ошибка изменения состояния: {error_text}")
    
    async def get_products(self) -> List[Dict]:
        """Получение списка товаров"""
        url = f"{self.base_url}entity/product"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('rows', [])
                else:
                    logger.error(f"❌ Ошибка получения товаров: {response.status}")
                    return []
    
    async def get_agent_by_name(self, name: str) -> Optional[str]:
        """Поиск контрагента по имени"""
        url = f"{self.base_url}entity/counterparty"
        params = {"filter": f"name={name}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    rows = data.get('rows', [])
                    if rows:
                        return rows[0]['meta']['href']
                return None
    
    async def find_agent_by_name(self, agent_name: str) -> str:
        """Поиск контрагента по имени"""
        try:
            # Загружаем локальный JSON с агентами
            agents_file = "data/AgentNameHref.json"
            
            # Читаем файл с обработкой ошибок
            try:
                with open(agents_file, "r", encoding="utf-8") as f:
                    agents = json.load(f)
            except FileNotFoundError:
                # Если файла нет, создаем его
                await self._save_all_agents_to_json(agents_file)
                with open(agents_file, "r", encoding="utf-8") as f:
                    agents = json.load(f)
            
            # Если JSON пустой, обновляем его (как в старом проекте)
            if not agents:
                await self._save_all_agents_to_json(agents_file)
                with open(agents_file, "r", encoding="utf-8") as f:
                    agents = json.load(f)
            
            # Ищем агента в локальном JSON
            print(f"🔍 Ищу агента: '{agent_name}' в {len(agents)} записях")
            href = self._smart_get(agents, agent_name)
            if href:
                return href
            
            # Если не найден, создаем нового (как в старом проекте)
            href = await self._create_agent(agent_name)
            return href
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска агента: {e}")
            return None
    
    def _smart_get(self, agents: dict, search_key: str) -> str:
        """Умный поиск агента по частичному совпадению"""
        for name, href in agents.items():
            if search_key.lower() in name.lower():
                return href
        return None
    
    async def _create_agent(self, agent_name: str) -> str:
        """Создание нового контрагента"""
        url = f"{self.base_url}entity/counterparty"
        payload = {
            "name": agent_name,
            "tags": ["auto-created"],
            "legalTitle": "",
            "type": "individual"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self.headers) as response:
                if response.status in (200, 201):
                    data = await response.json()
                    href = data["meta"]["href"]
                    logger.info(f"✅ Контрагент '{agent_name}' создан: {href}")
                    return href
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка создания контрагента: {error_text}")
                    return None
    
    async def _save_all_agents_to_json(self, json_file: str):
        """Сохранение всех агентов в JSON файл"""
        url = f"{self.base_url}entity/counterparty"
        all_agents = {}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    for agent in data.get("rows", []):
                        name = agent.get("name")
                        href = agent.get("meta", {}).get("href")
                        if name and href:
                            all_agents[name] = href
                    
                    # Сохраняем в JSON
                    with open(json_file, "w", encoding="utf-8") as f:
                        json.dump(all_agents, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"💾 Сохранено {len(all_agents)} контрагентов в {json_file}")

    async def _get_positions(self, items: List[Dict]) -> List[Dict]:
        """Получение позиций товаров для заказа"""
        try:
            # Загружаем JSON с товарами
            items_file = "data/ItemNameHref.json"
            
            try:
                with open(items_file, "r", encoding="utf-8") as f:
                    items_json = json.load(f)
            except FileNotFoundError:
                # Если файла нет, создаем его
                await self._save_all_items_to_json(items_file)
                with open(items_file, "r", encoding="utf-8") as f:
                    items_json = json.load(f)
            
            positions = []
            for item in items:
                item_href = self._smart_get_item(item['name'], items_json)
                if item_href:
                    position = {
                        "assortment": {
                            "meta": {
                                "href": item_href,
                                "type": "variant",
                                "mediaType": "application/json"
                            }
                        },
                        "quantity": item["quantity"],
                        "price": int(item["price"] / item["quantity"] * 100000)  # Цена за единицу в копейках
                    }
                    positions.append(position)

                else:
                    print(f"❌ Товар не найден: {item['name']}")
            
            return positions
            
        except Exception as e:
            print(f"❌ Ошибка получения позиций: {e}")
            return []

    def _smart_get_item(self, item_name: str, items_json: dict) -> str:
        """Умный поиск товара по имени"""
        search_words = item_name.strip().lower().split()
        for name, href in items_json.items():
            full_name = name.lower()
            if all(word in full_name for word in search_words):
                return href
        return None

    async def _save_all_items_to_json(self, json_file: str):
        """Сохранение всех товаров в JSON файл с пагинацией"""
        url = f"{self.base_url}entity/variant"
        all_items = {}
        next_url = url
        
        async with aiohttp.ClientSession() as session:
            while next_url:
                async with session.get(next_url, headers=self.headers) as response:
                    if response.status != 200:
                        print(f"❌ Ошибка при запросе: {response.status}")
                        break
                    
                    data = await response.json()
                    for item in data.get("rows", []):
                        name = item.get("name")
                        href = item.get("meta", {}).get("href")
                        if name and href:
                            all_items[name] = href
                    
                    # Получаем следующую страницу
                    next_url = data.get("meta", {}).get("nextHref")
            
            # Сохраняем в JSON
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(all_items, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Сохранено {len(all_items)} товаров в {json_file}")

