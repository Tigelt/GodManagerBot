import requests
import json
import os
from configMC import headers, IvanActual_href, DATA_DIR, ACTUAL_BRANDS

def get_stock_data():
    """Получает остатки со склада"""
    try:
        print("🔄 Получаю остатки со склада...")
        
        # URL для получения остатков по складам
        url = "https://api.moysklad.ru/api/remap/1.2/report/stock/bystore"
        
        # Фильтр по нашему складу
        params = {
            "filter": f"store={IvanActual_href}"
        }
        
        print(f"🔍 Запрашиваю остатки по складу: {IvanActual_href}")
        
        # Делаем запрос к API
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Получено {data['meta']['size']} товаров с остатками")
            
            # Сохраняем сырые данные остатков
            stock_file = f"{DATA_DIR}StockData.json"
            with open(stock_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Остатки сохранены в {stock_file}")
            
            # Возвращаем данные для дальнейшей обработки
            return data
            
        else:
            error_msg = f"Ошибка API: {response.status_code}"
            print(f"❌ {error_msg}")
            return None
        
    except Exception as e:
        print(f"❌ Ошибка получения остатков: {e}")
        return None

async def prepareAssortment():
    """Подготавливает ассортимент - тянет остатки со склада и создает FinalAssortment"""
    try:
        # Получаем остатки со склада
        stock_data = get_stock_data()
        
        if not stock_data:
            print("❌ Не удалось получить остатки")
            return None
        
        print("✅ Остатки получены успешно")
        
        # Загружаем словарь название → href
        name_href_file = f"{DATA_DIR}ItemNameHref.json"
        with open(name_href_file, "r", encoding="utf-8") as f:
            name_to_href = json.load(f)
        
        # Создаем обратный словарь href → название
        href_to_name = {href: name for name, href in name_to_href.items()}
        
        print(f"📚 Загружено {len(href_to_name)} товаров из словаря")
        
        # Загружаем описания вкусов
        flavor_descriptions_file = f"{DATA_DIR}FlavorDescriptions.json"
        flavor_descriptions = {}
        try:
            with open(flavor_descriptions_file, "r", encoding="utf-8") as f:
                flavor_descriptions = json.load(f)
            print(f"📚 Загружено описаний вкусов для {len(flavor_descriptions)} брендов")
        except Exception as e:
            print(f"⚠️ Не удалось загрузить описания вкусов: {e}")
        
        # Создаем финальный ассортимент как словарь
        final_assortment = {}
        
        # Идем по массиву актуальных брендов
        for brand in ACTUAL_BRANDS:
            print(f"🔍 Обрабатываю бренд: {brand}")
            
            # Создаем структуру для бренда
            brand_data = {
                "whole_packs": [],
                "loose_packs": []
            }
            
            # Идем по остаткам со склада
            if "rows" in stock_data:
                for item in stock_data["rows"]:
                    # Получаем href товара
                    item_href = get_item_href(item)
                    
                    # Получаем доступное количество
                    available = get_available_quantity(item)
                    
                    # Если товар есть в словаре и количество > 0
                    if item_href in href_to_name and available > 0:
                        item_name = href_to_name[item_href]
                        
                        # Проверяем, принадлежит ли товар этому бренду
                        if is_item_belongs_to_brand(item_name, brand):
                            # Очищаем название от бренда и веса
                            clean_name = clean_item_name(item_name, brand)
                            
                            # Ищем ссылку на описание вкуса
                            flavor_link = find_flavor_link(brand, clean_name, flavor_descriptions)
                            
                            # Проверяем, заканчивается ли на "1г"
                            if item_name.endswith("1г") or item_name.endswith("(1г)"):
                                # Наразвес - округляем до кратного 25
                                rounded_quantity = round_to_nearest_25(available)
                                if rounded_quantity >= 25:  # Показываем только если >= 25г
                                    # Создаем объект вкуса для loose_packs
                                    flavor_data = {
                                        "name": clean_name,
                                        "quantity": rounded_quantity,
                                        "link": flavor_link
                                    }
                                    brand_data["loose_packs"].append(flavor_data)
                                    link_info = f" (ссылка: {flavor_link})" if flavor_link else " (без ссылки)"
                                    print(f"  📦 Наразвес: {clean_name} - {available}г → {rounded_quantity}г{link_info}")
                                else:
                                    print(f"  📦 Наразвес: {clean_name} - {available}г → не показываем (< 25г)")
                            else:
                                # Целые пачки
                                # Создаем объект вкуса для whole_packs
                                flavor_data = {
                                    "name": clean_name,
                                    "quantity": available,
                                    "link": flavor_link
                                }
                                brand_data["whole_packs"].append(flavor_data)
                                link_info = f" (ссылка: {flavor_link})" if flavor_link else " (без ссылки)"
                                print(f"  📦 Целая пачка: {clean_name} - {available}{link_info}")
            
            # Добавляем бренд в финальный ассортимент, если есть товары
            if brand_data["whole_packs"] or brand_data["loose_packs"]:
                final_assortment[brand] = brand_data
                whole_count = len(brand_data["whole_packs"])
                loose_count = len(brand_data["loose_packs"])
                print(f"✅ Бренд {brand}: {whole_count} целых пачек, {loose_count} наразвес")
        
        # Сохраняем финальный ассортимент
        final_file = f"{DATA_DIR}FinalAssortment.json"
        with open(final_file, "w", encoding="utf-8") as f:
            json.dump(final_assortment, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Финальный ассортимент сохранен в {final_file}")
        print(f"📊 Обработано брендов: {len(final_assortment)}")
        
        return final_assortment
        
    except Exception as e:
        print(f"❌ Ошибка подготовки ассортимента: {e}")
        return None

def get_available_quantity(item):
    """Вычисляет доступное количество (остаток - резерв)"""
    available = 0
    if "stockByStore" in item:
        for store_stock in item["stockByStore"]:
            stock = store_stock.get("stock", 0)
            reserve = store_stock.get("reserve", 0)
            available += (stock - reserve)
    return int(available)

def get_item_href(item):
    """Получает чистый href товара без параметров"""
    item_href = item.get("meta", {}).get("href", "")
    
    # Убираем параметры из href (всё после ?)
    if "?" in item_href:
        item_href = item_href.split("?")[0]
    
    return item_href

def is_item_belongs_to_brand(item_name, brand):
    """Проверяет, принадлежит ли товар указанному бренду"""
    item_lower = item_name.lower()
    brand_lower = brand.lower()
    
    # СПЕЦИАЛЬНЫЕ СЛУЧАИ - проверяем сначала более специфичные бренды
    if brand == "Darkside Xperience":
        # Для Xperience ищем только товары с "xperience" или "darkside xperience"
        return "xperience" in item_lower or "darkside xperience" in item_lower
    elif brand == "Darkside":
        # Для обычного Darkside исключаем товары с "xperience"
        if "xperience" in item_lower:
            return False
        return "darkside" in item_lower
    elif brand == "DS shot":
        # Для DS shot ищем только товары с "ds shot"
        return "ds shot" in item_lower
    elif brand == "Blackburn":
        # Для Blackburn ищем только товары с "blackburn"
        return "blackburn" in item_lower
    elif brand == "Overdose":
        # Для Overdose ищем только товары с "overdose", но исключаем "blackburn ovd"
        if "blackburn" in item_lower:
            return False
        return "overdose" in item_lower
    
    # Обычная логика для остальных брендов
    brand_variants = [
        brand_lower,
        brand_lower.replace(" ", ""),
        brand_lower.replace(" ", "_"),
        brand_lower.replace(" ", "-")
    ]
    
    # Проверяем, содержит ли название товара любой из вариантов бренда
    return any(variant in item_lower for variant in brand_variants)

def clean_item_name(item_name, brand):
    """Очищает название товара от бренда и веса"""
    import re
    clean_name = item_name
    
    # Специальная логика для DS Shot
    if brand == "DS shot":
        # Убираем "DS Shot" из начала названия
        clean_name = re.sub(r'^DS\s+Shot\s+', '', clean_name, flags=re.IGNORECASE)
    elif brand == "Xperience":
        # Убираем "Darkside Xperience" из начала названия
        clean_name = re.sub(r'^Darkside\s+Xperience\s+', '', clean_name, flags=re.IGNORECASE)
    else:
        # Обычная логика для других брендов
        brand_variants = [brand, brand.replace(" ", ""), brand.replace(" ", "_")]
        for variant in brand_variants:
            if variant.lower() in clean_name.lower():
                clean_name = clean_name.replace(variant, "").strip()
                break
    
    # Убираем вес в скобках
    clean_name = re.sub(r'\s*\(\d+г\)', '', clean_name)
    clean_name = re.sub(r'\s*\d+г', '', clean_name)
    clean_name = re.sub(r'\s*\(1г\)', '', clean_name)
    clean_name = re.sub(r'\s*1г', '', clean_name)
    
    return clean_name.strip()

def round_to_nearest_25(quantity):
    """Округляет количество до ближайшего кратного 25 (в меньшую сторону)"""
    if quantity < 25:
        return 0
    
    # Округляем в меньшую сторону до кратного 25
    return (quantity // 25) * 25

def find_flavor_link(brand_name, flavor_name, flavor_descriptions):
    """Ищет ссылку на описание вкуса - ТОЧНОЕ СОВПАДЕНИЕ В НИЖНЕМ РЕГИСТРЕ"""
    if brand_name in flavor_descriptions:
        brand_flavors = flavor_descriptions[brand_name]
        
        # Точное совпадение в нижнем регистре
        flavor_name_lower = flavor_name.lower()
        for desc_flavor_name, link in brand_flavors.items():
            if desc_flavor_name.lower() == flavor_name_lower:
                return link
                
    return None
