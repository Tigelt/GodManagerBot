"""
Обработчик команд ассортимента
"""

import asyncio
import json
import re
import logging
import aiohttp
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from services.telegram_client import TelegramClientService
from services.moy_sklad import MoySkladAPI

logger = logging.getLogger(__name__)

class AssortmentHandler:
    """Обработчик команд ассортимента"""
    
    def __init__(self, telegram_client: TelegramClientService, moy_sklad: MoySkladAPI, config: dict):
        self.telegram_client = telegram_client
        self.moy_sklad = moy_sklad
        self.config = config
        self.auto_publish_running = False
    
    async def handle_assortment_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /assortment"""
        try:
            await update.message.reply_text("🔄 Подготавливаю ассортимент...")
            
            # Подготавливаем ассортимент
            final_assortment = await self._prepare_assortment()
            if not final_assortment:
                await update.message.reply_text("❌ Не удалось подготовить ассортимент")
                return
            
            await update.message.reply_text("🔄 Публикую ассортимент, пожалуйста ожидайте...")
            
            # Публикуем ассортимент
            await self._publish_assortment(final_assortment, update, context)
            
            await update.message.reply_text("✅ Ассортимент успешно добавлен!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки команды /assortment: {e}")
            await update.message.reply_text("❌ Ошибка публикации ассортимента")
    
    async def handle_update_assortment_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /updateassortment"""
        try:
            await update.message.reply_text("🔄 Обновляю ассортимент...")
            
            # Сначала обновляем данные из Мой Склад
            await self._prepare_assortment()
            
            # Потом обновляем сообщения в форуме
            await self._update_assortment(update, context)
            
            await update.message.reply_text("✅ Ассортимент успешно обновлен!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки команды /updateassortment: {e}")
            await update.message.reply_text("❌ Ошибка обновления ассортимента")
    
    async def handle_base_flavor_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /baseflavor - обновляет описания вкусов из Telegram канала"""
        try:
            print("🔄 Обновляю описания вкусов...")
            await update.message.reply_text("🔄 Обновляю описания вкусов...")
            
            # Получаем информацию о канале с описаниями
            entity = await self.telegram_client.get_entity(self.config['flavor_channel'])
            
            # Получаем все сообщения в ветке с описаниями
            messages = []
            async for message in self.telegram_client.iter_messages(
                entity, 
                reply_to=self.config['flavor_thread_id'], 
                limit=None
            ):
                if message.text:  # Только сообщения с текстом
                    messages.append(message)
            
            
            # Создаем структуру для хранения описаний вкусов
            flavor_descriptions = {}
            
            # Бренды из конфига
            actual_brands = self.config['actual_brands']
            
            # Идем по массиву актуальных брендов
            for brand in actual_brands:
                
                
                # Создаем хештег для поиска (в нижнем регистре, убираем пробелы, апострофы и 's')
                hashtag = f"#{brand.lower().replace(' ', '').replace(chr(39), '')}"
                
                # Ищем сообщения с этим хештегом
                brand_messages = []
                for message in messages:
                    if message.text and hashtag in message.text.lower():
                        brand_messages.append(message)
                
                print(f"📝 Найдено {len(brand_messages)} сообщений для {brand}")
                
                # Обрабатываем найденные сообщения
                if brand_messages:
                    flavor_descriptions[brand] = {}
                    
                    for message in brand_messages:
                        # Берем первую строку как название вкуса и убираем звездочки
                        lines = message.text.strip().split('\n')
                        if lines:
                            flavor_name = lines[0].strip().replace('**', '')
                            
                            # Создаем ссылку на сообщение
                            message_link = f"https://t.me/{entity.username}/{message.id}"
                            
                            # Добавляем в структуру
                            flavor_descriptions[brand][flavor_name] = message_link
                            logger.info(f"  ✅ {flavor_name} → {message_link}")
                
                # Если не нашли сообщения для бренда, создаем пустую секцию
                if brand not in flavor_descriptions:
                    flavor_descriptions[brand] = {}
                    print(f"  ⚠️ Не найдено сообщений для {brand}")
                    
            # Убираем секцию "Остальные" - нам нужны только бренды из массива
            
            # Сохраняем результат в JSON файл
            output_file = self.config['flavor_descriptions_file']
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(flavor_descriptions, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Описания вкусов сохранены в {output_file}")
            
            # Отправляем результат в чат
            total_flavors = sum(len(flavors) for flavors in flavor_descriptions.values())
            result_message = f"✅ Обновление описаний вкусов завершено!\n\n"
            result_message += f"📊 Статистика:\n"
            result_message += f"• Брендов: {len(flavor_descriptions)}\n"
            result_message += f"• Всего вкусов: {total_flavors}\n\n"
            
            for brand, flavors in flavor_descriptions.items():
                if flavors:
                    result_message += f"• {brand}: {len(flavors)} вкусов\n"
            
            await update.message.reply_text(result_message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки команды /baseflavor: {e}")
            await update.message.reply_text(f"❌ Ошибка обновления описаний вкусов: {str(e)}")
    
    async def handle_inventory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /inventory - показывает инвентарь табаков"""
        try:
            await update.message.reply_text("🔄 Загружаю инвентарь...")
            
            # Подготавливаем ассортимент (как в _publish_assortment)
            final_assortment = await self._prepare_assortment()
            if not final_assortment:
                await update.message.reply_text("❌ Не удалось подготовить ассортимент")
                return
            
            # Отправляем каждый бренд отдельным сообщением (как в _publish_assortment)
            for brand_name, brand_data in final_assortment.items():
                whole_packs = brand_data.get("whole_packs", [])
                loose_packs = brand_data.get("loose_packs", [])
                
                if whole_packs or loose_packs:
                    # Формируем сообщение для бренда (как в _format_brand_message)
                    message = self._format_inventory_message(brand_name, whole_packs, loose_packs)
                    
                    # Отправляем в чат с ботом
                    await update.message.reply_text(message)
                    
                    # Задержка между сообщениями
                    await asyncio.sleep(1)
            
            await update.message.reply_text("✅ Инвентарь загружен!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки команды /inventory: {e}")
            await update.message.reply_text("❌ Ошибка загрузки инвентаря")
    
    async def _prepare_assortment(self):
        """Подготавливает ассортимент - тянет остатки со склада и создает FinalAssortment"""
        try:
            print("🔄 Начинаю подготовку ассортимента...")
            
            # Получаем остатки со склада
            
            stock_data = await self._get_stock_data()
            if not stock_data:
                print("❌ Не удалось получить остатки")
                logger.error("❌ Не удалось получить остатки")
                return None
            
        
            # Загружаем словарь название → href
            name_href_file = self.config['item_name_href_file']
            try:
                with open(name_href_file, "r", encoding="utf-8") as f:
                    name_to_href = json.load(f)
                
            except Exception as e:
                print(f"❌ Не удалось загрузить ItemNameHref.json: {e}")
                
                return None
            
            # Создаем обратный словарь href → название
            href_to_name = {href: name for name, href in name_to_href.items()}
            
            # Загружаем описания вкусов
            flavor_descriptions_file = self.config['flavor_descriptions_file']
            flavor_descriptions = {}
            try:
                with open(flavor_descriptions_file, "r", encoding="utf-8") as f:
                    flavor_descriptions = json.load(f)
                
            except Exception as e:
                logger.warning(f"⚠️ Не удалось загрузить описания вкусов: {e}")
            
            # Создаем финальный ассортимент как словарь
            final_assortment = {}
            
            # Идем по массиву актуальных брендов
            for brand in self.config['actual_brands']:
                
                
                # Создаем структуру для бренда
                brand_data = {
                    "whole_packs": [],
                    "loose_packs": []
                }
                
                # Идем по остаткам со склада
                if "rows" in stock_data:
                    for item in stock_data["rows"]:
                        # Получаем href товара
                        item_href = self._get_item_href(item)
                        
                        # Получаем доступное количество
                        available = self._get_available_quantity(item)
                        
                        # Если товар есть в словаре и количество > 0
                        if item_href in href_to_name and available > 0:
                            item_name = href_to_name[item_href]
                            
                            # Проверяем, принадлежит ли товар этому бренду
                            if self._is_item_belongs_to_brand(item_name, brand):
                                # Очищаем название от бренда и веса
                                clean_name = self._clean_item_name(item_name, brand)
                                
                                # Ищем ссылку на описание вкуса
                                flavor_link = self._find_flavor_link(brand, clean_name, flavor_descriptions)
                                
                                # Проверяем, заканчивается ли на "1г"
                                if item_name.endswith("1г") or item_name.endswith("(1г)"):
                                    # Наразвес - округляем до кратного 25
                                    rounded_quantity = self._round_to_nearest_25(available)
                                    if rounded_quantity >= 25:  # Показываем только если >= 25г
                                        # Создаем объект вкуса для loose_packs
                                        flavor_data = {
                                            "name": clean_name,
                                            "quantity": rounded_quantity,
                                            "link": flavor_link
                                        }
                                        brand_data["loose_packs"].append(flavor_data)
                                        link_info = f" (ссылка: {flavor_link})" if flavor_link else " (без ссылки)"
                                        
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
                                    
                
                # Добавляем бренд в финальный ассортимент, если есть товары
                if brand_data["whole_packs"] or brand_data["loose_packs"]:
                    # Сортируем товары внутри бренда по названию
                    brand_data["whole_packs"].sort(key=lambda x: x["name"])
                    brand_data["loose_packs"].sort(key=lambda x: x["name"])
                    final_assortment[brand] = brand_data
                    whole_count = len(brand_data["whole_packs"])
                    loose_count = len(brand_data["loose_packs"])
                    
            
            # Сохраняем финальный ассортимент
            final_file = self.config['final_assortment_file']
            with open(final_file, "w", encoding="utf-8") as f:
                json.dump(final_assortment, f, ensure_ascii=False, indent=2)
            
            
            return final_assortment
            
        except Exception as e:
            logger.error(f"❌ Ошибка подготовки ассортимента: {e}")
            return None
    
    async def _get_stock_data(self):
        """Получает остатки со склада асинхронно"""
        try:
            logger.info("🔄 Получаю остатки со склада...")
            
            # URL для получения остатков по складам
            url = "https://api.moysklad.ru/api/remap/1.2/report/stock/bystore"
            
            # Фильтр по нашему складу (TODO: добавить в конфиг)
            store_href = "https://api.moysklad.ru/api/remap/1.2/entity/store/5b0a00a8-3b99-11f0-0a80-09fd0007829f"
            params = {
                "filter": f"store={store_href}"
            }
            
            
            
            # Делаем асинхронный запрос к API
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.config["moy_sklad_token"]}',
                    'Content-Type': 'application/json'
                }
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        
                        # Сохраняем сырые данные остатков
                        stock_file = self.config['stock_data_file']
                        with open(stock_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        
                        
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка API: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Ошибка получения остатков: {e}")
            return None
    
    def _get_available_quantity(self, item):
        """Вычисляет доступное количество (остаток - резерв)"""
        available = 0
        if "stockByStore" in item:
            for store_stock in item["stockByStore"]:
                stock = store_stock.get("stock", 0)
                reserve = store_stock.get("reserve", 0)
                available += (stock - reserve)
        return int(available)
    
    def _get_item_href(self, item):
        """Получает чистый href товара без параметров"""
        item_href = item.get("meta", {}).get("href", "")
        
        # Убираем параметры из href (всё после ?)
        if "?" in item_href:
            item_href = item_href.split("?")[0]
        
        return item_href
    
    def _is_item_belongs_to_brand(self, item_name, brand):
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
    
    def _clean_item_name(self, item_name, brand):
        """Очищает название товара от бренда и веса"""
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
    
    def _round_to_nearest_25(self, quantity):
        """Округляет количество до ближайшего кратного 25 (в меньшую сторону)"""
        if quantity < 25:
            return 0
        
        # Округляем в меньшую сторону до кратного 25
        return (quantity // 25) * 25
    
    def _find_flavor_link(self, brand_name, flavor_name, flavor_descriptions):
        """Ищет ссылку на описание вкуса - ТОЧНОЕ СОВПАДЕНИЕ В НИЖНЕМ РЕГИСТРЕ"""
        if brand_name in flavor_descriptions:
            brand_flavors = flavor_descriptions[brand_name]
            
            # Точное совпадение в нижнем регистре
            flavor_name_lower = flavor_name.lower()
            for desc_flavor_name, link in brand_flavors.items():
                if desc_flavor_name.lower() == flavor_name_lower:
                    return link
                    
        return None
    
    async def _publish_assortment(self, final_assortment, update=None, context=None):
        """Публикация ассортимента в форум"""
        try:
            print(f"📤 Публикую ассортимент: {len(final_assortment)} брендов")
            
            # Сначала очищаем форум (оставляем только главное сообщение)
            main_message_id = await self._clear_forum_except_oldest()
            
            # Словарь для хранения ссылок на бренды
            brand_links = {}
            
            # Отправляем каждый бренд отдельным сообщением
            for brand_name, brand_data in final_assortment.items():
                whole_packs = brand_data.get("whole_packs", [])
                loose_packs = brand_data.get("loose_packs", [])
                
                if whole_packs or loose_packs:
                    # Формируем сообщение для бренда
                    message = self._format_brand_message(brand_name, whole_packs, loose_packs)
                    
                    # Отправляем в форум через Telethon
                    try:
                        sent_message = await self.telegram_client.send_message(
                            chat_id=self.config['forum_chat_id'],
                            message=message,
                            thread_id=self.config['forum_thread_id']
                        )
                        print(f"✅ Отправлен в форум: {brand_name} (Целых пачек: {len(whole_packs)} Наразвес: {len(loose_packs)} товаров)")
                        
                        # Отправляем уведомление в личный чат с ботом
                        if update and context:
                            try:
                                notification_text = f"🔄 Обновлено: {brand_name} - {len(whole_packs) + len(loose_packs)} товаров"
                                await update.message.reply_text(notification_text)
                        
                            except Exception as notification_error:
                                print(f"⚠️ Ошибка отправки уведомления: {notification_error}")
                        
                        # Создаем ссылку на сообщение
                        entity = await self.telegram_client.get_entity(self.config['forum_chat_id'])
                        chat_id_numeric = entity.id
                        message_link = f"https://t.me/c/{chat_id_numeric}/{sent_message.id}"
                        brand_links[brand_name] = message_link
                        
                        # Задержка между сообщениями
                        import asyncio
                        await asyncio.sleep(4)
                        
                    except Exception as forum_error:
                        print(f"❌ Ошибка отправки в форум: {forum_error}")
            
            # Выводим все собранные ссылки
            print(f"\n📋 ДИНАМИЧЕСКИЙ СЛОВАРИК ССЫЛОК:")
            for brand, link in brand_links.items():
                print(f"   {brand}: {link}")
            
            # Обновляем главное сообщение с гиперссылками
            if self.config['forum_chat_id'] and brand_links and main_message_id:
                await self._update_main_message_with_links(main_message_id, brand_links)
            
            print(f"🎉 Публикация завершена!")
            
        except Exception as e:
            print(f"❌ Ошибка публикации ассортимента: {e}")
            raise e
    
    def _format_brand_message(self, brand_name, whole_packs, loose_packs):
        """Форматирование сообщения для бренда"""
        # Заголовок с квадратиками по бокам и жирным названием бренда заглавными буквами
        message = f"▪️▪️▪️**{brand_name.upper()}**▪️▪️▪️\n\n"
        
        # Сначала выводим целые баночки
        for flavor in whole_packs:
            name = flavor.get("name", "")
            quantity = flavor.get("quantity", 0)
            link = flavor.get("link")
            
            # Ограничиваем количество до 3+
            display_quantity = "3+" if quantity > 3 else str(quantity)
            
            if link:
                # Добавляем гиперссылку
                message += f"[{name}]({link}) {display_quantity}\n"
            else:
                # Без гиперссылки, обычное название
                message += f"{name} {display_quantity}\n"
        
        # Добавляем разделитель и вскрытые вкусы, если есть
        if loose_packs:
            message += "\n---\n**Вскрытые вкусы:**\n"
            
            for flavor in loose_packs:
                name = flavor.get("name", "")
                quantity = flavor.get("quantity", 0)
                link = flavor.get("link")
                
                if link:
                    # Добавляем гиперссылку с количеством грамм
                    message += f"[{name}]({link}) {quantity}г\n"
                else:
                    # Без гиперссылки, обычное название с количеством грамм
                    message += f"{name} {quantity}г\n"
        
        return message
    
    def _format_inventory_message(self, brand_name, whole_packs, loose_packs):
        """Форматирование сообщения для инвентаря - только целые пачки"""
        # Заголовок с квадратиками по бокам и жирным названием бренда заглавными буквами
        message = f"▪️▪️▪️{brand_name.upper()}▪️▪️▪️\n\n"
        
        # Показываем только целые пачки
        total_quantity = 0
        for flavor in whole_packs:
            name = flavor.get("name", "")
            quantity = flavor.get("quantity", 0)
            total_quantity += quantity
            
            # Показываем точное количество
            message += f"{name} {quantity}\n"
        
        # Добавляем суммарное количество в конце
        if total_quantity > 0:
            message += f"\nВсего: {total_quantity} шт"
        
        return message
    
    async def _clear_forum_except_oldest(self):
        """Очищает форум, оставляя только самое старое сообщение"""
        try:
            # Получаем все сообщения в форуме
            messages = []
            async for message in self.telegram_client.iter_messages(
                self.config['forum_chat_id'], 
                reply_to=self.config['forum_thread_id'], 
                limit=None
            ):
                messages.append(message)
            
            
            for i, message in enumerate(messages):
                text_preview = message.text[:50] if message.text else "Нет текста"
                print(f"   {i}: ID {message.id} | Дата: {message.date} | Текст: {text_preview}...")
            
            if len(messages) <= 1:
                print("✅ В форуме только одно сообщение, очистка не нужна")
                return None
            
            # Находим главное сообщение (с текстом, самое старое)
            main_messages = [m for m in messages if m.text and len(m.text) > 10]
            if not main_messages:
                print("❌ Не найдено главное сообщение с текстом!")
                return None
            
            main_message = min(main_messages, key=lambda m: m.date)
            
            # Удаляем все сообщения кроме главного
            deleted_count = 0
            for message in messages:
                if message.id == main_message.id:  # Пропускаем главное сообщение
                    
                    continue
                
                try:
                    await self.telegram_client.delete_message(
                        chat_id=self.config['forum_chat_id'],
                        message_id=message.id
                    )
                    deleted_count += 1
                    print(f"🗑️ Удалено сообщение ID {message.id}")
                except Exception as e:
                    print(f"❌ Не удалось удалить сообщение ID {message.id}: {e}")
            
            print(f"✅ Очистка завершена! Удалено {deleted_count} сообщений")
            return main_message.id
            
        except Exception as e:
            print(f"❌ Ошибка очистки форума: {e}")
            return None
    
    async def _update_main_message_with_links(self, main_message_id, brand_links):
        """Обновляет главное сообщение, добавляя гиперссылки к названиям брендов"""
        try:
            # Получаем главное сообщение
            main_message = await self.telegram_client.get_message(
                chat_id=self.config['forum_chat_id'],
                message_id=main_message_id
            )
            
            if not main_message:
                print(f"❌ Не удалось получить главное сообщение ID {main_message_id}")
                return
            
            current_text = main_message.text
            
            
            # Удаляем все старые гиперссылки
            import re
            updated_text = current_text
            
            # Удаляем жирный текст **
            updated_text = re.sub(r'\*\*', '', updated_text)
            
            
            # Удаляем все гиперссылки в формате [текст](ссылка)
            updated_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', updated_text)
            
            
            # Добавляем новые гиперссылки
            # Сортируем по длине названия (от длинного к короткому)
            sorted_brands = sorted(brand_links.items(), key=lambda x: len(x[0]), reverse=True)
            
            for brand_name, link in sorted_brands:
                # Создаем гиперссылку в формате Markdown
                hyperlink = f"[{brand_name}]({link})"
                
                # Заменяем в тексте
                if brand_name in updated_text:
                    updated_text = updated_text.replace(brand_name, hyperlink)
                    print(f"🔗 Заменено '{brand_name}' на гиперссылку")
                else:
                    print(f"⚠️ Не найдено '{brand_name}' в тексте")
            
            # Восстанавливаем жирный текст в начале и конце
            if not updated_text.startswith('**'):
                updated_text = '**' + updated_text
            if not updated_text.endswith('**'):
                updated_text = updated_text + '**'
            
            # Отправляем обновленное сообщение
            await self.telegram_client.edit_message(
                chat_id=self.config['forum_chat_id'],
                message_id=main_message_id,
                text=updated_text
            )
            print(f"✅ Главное сообщение обновлено с гиперссылками!")
            
        except Exception as e:
            print(f"❌ Ошибка обновления главного сообщения: {e}")
    
    async def _update_assortment(self, update=None, context=None):
        """Обновляет содержимое существующих сообщений с ассортиментом (после отгрузки)"""
        try:
            print("🔄 Начинаю обновление ассортимента...")
            
            # Загружаем финальный ассортимент
            final_file = self.config['final_assortment_file']
            try:
                with open(final_file, "r", encoding="utf-8") as f:
                    assortment_data = json.load(f)
                print(f"📦 Загружен СВЕЖИЙ ассортимент: {len(assortment_data)} брендов")
            except FileNotFoundError:
                print("❌ Файл ассортимента не найден!")
                return
            
            # Загружаем описания вкусов с ссылками
            flavor_descriptions_file = self.config['flavor_descriptions_file']
            flavor_descriptions = {}
            try:
                with open(flavor_descriptions_file, "r", encoding="utf-8") as f:
                    flavor_descriptions = json.load(f)
                print(f"📚 Загружены описания вкусов: {len(flavor_descriptions)} брендов")
            except FileNotFoundError:
                print("⚠️ Файл описаний вкусов не найден, гиперссылки не будут добавлены")
            
            # Получаем все сообщения в форуме
            messages = []
            async for message in self.telegram_client.iter_messages(
                self.config['forum_chat_id'], 
                reply_to=self.config['forum_thread_id'], 
                limit=None
            ):
                if message.text:  # Только сообщения с текстом
                    messages.append(message)
            
            print(f"📋 Найдено {len(messages)} сообщений в форуме")
            
            # Сортируем сообщения по дате (от старых к новым)
            messages.sort(key=lambda x: x.date)
            
            # Пропускаем первое сообщение (главное) - оно не изменяется
            brand_messages = messages[1:]  # Сообщения с брендами
            
            
            
            # Обновляем каждое сообщение с брендом
            for i, (brand_name, brand_data) in enumerate(assortment_data.items()):
                if i >= len(brand_messages):
                    print(f"⚠️ Недостаточно сообщений для бренда {i+1}")
                    break
                    
                whole_packs = brand_data.get("whole_packs", [])
                loose_packs = brand_data.get("loose_packs", [])
                
                # Проверяем что есть товары для отображения
                if whole_packs or loose_packs:
                    # Формируем новое сообщение для бренда с гиперссылками
                    new_message = self._format_brand_message(brand_name, whole_packs, loose_packs)
                    
                    # Получаем сообщение для обновления
                    message_to_update = brand_messages[i]
                    
                    # Показываем детали изменений
                    whole_packs_count = len(whole_packs)
                    loose_packs_count = len(loose_packs)
                    
                    
                    try:
                        # Обновляем сообщение
                        await self.telegram_client.edit_message(
                            chat_id=self.config['forum_chat_id'],
                            message_id=message_to_update.id,
                            text=new_message
                        )
                        
                        print(f"✅ Обновлено сообщение {i+1}: {brand_name} ({whole_packs_count + loose_packs_count} товаров)")
                        
                        # Отправляем уведомление о успешном обновлении в личный чат
                        if update and context:
                            try:
                                notification_text = f"🔄 Обновлено: {brand_name} - {whole_packs_count + loose_packs_count} товаров"
                                await update.message.reply_text(notification_text)
                                
                            except Exception as notification_error:
                                print(f"⚠️ Ошибка отправки уведомления: {notification_error}")
                        
                        # Задержка между обновлениями
                        import asyncio
                        await asyncio.sleep(5)
                        
                    except Exception as e:
                        error_msg = str(e)
                        if "Content of the message was not modified" in error_msg:
                            print(f"ℹ️ Сообщение {i+1}: {brand_name} - без изменений")
                            
                            # Отправляем уведомление что табак не изменился в личный чат
                            if update and context:
                                try:
                                    notification_text = f"ℹ️ {brand_name} не изменен."
                                    await update.message.reply_text(notification_text)
                                    
                                except Exception as notification_error:
                                    print(f"⚠️ Ошибка отправки уведомления: {notification_error}")
                        else:
                            print(f"❌ Ошибка обновления сообщения {i+1}: {e}")
            
            
            
            # Обновляем главное сообщение с гиперссылками
            if messages and len(messages) > 0:
                main_message_id = messages[0].id  # Первое сообщение - главное
                print(f"🔍 Главное сообщение ID: {main_message_id}")
                
                # Собираем ссылки на бренды из существующих сообщений форума
                brand_links = {}
                print(f"🔍 Ищу ссылки для {len(assortment_data)} брендов в {len(brand_messages)} сообщениях")
                
                # Получаем entity для создания ссылок
                entity = await self.telegram_client.get_entity(self.config['forum_chat_id'])
                chat_id_numeric = entity.id
                
                for i, (brand_name, brand_data) in enumerate(assortment_data.items()):
                    if i < len(brand_messages):
                        message = brand_messages[i]
                        # Создаем ссылку на сообщение
                        message_link = f"https://t.me/c/{chat_id_numeric}/{message.id}"
                        brand_links[brand_name] = message_link
                        print(f"🔍 Бренд '{brand_name}': ссылка = {message_link}")
                
                print(f"🔍 Найдено {len(brand_links)} ссылок: {list(brand_links.keys())}")
                if brand_links:
                    await self._update_main_message_with_links(main_message_id, brand_links)
                    print("🔗 Главное сообщение обновлено с гиперссылками!")
                else:
                    print("⚠️ Ссылки не найдены, главное сообщение не обновляется")
            
        except Exception as e:
            print(f"❌ Критическая ошибка обновления ассортимента: {e}")
    
    async def start_auto_publish(self):
        """Запуск автоматической публикации ассортимента"""
        if self.auto_publish_running:
            logger.warning("Автопубликация уже запущена")
            return
        
        self.auto_publish_running = True
        logger.info("🕐 Автопубликация ассортимента запущена (12:00 UTC+7)")
        print("🕐 Автопубликация ассортимента запущена (12:00 UTC+7)")
        
        # Запускаем фоновую задачу
        asyncio.create_task(self._auto_publish_loop())
    
    async def _auto_publish_loop(self):
        """Фоновый цикл автопубликации ассортимента"""
        while self.auto_publish_running:
            try:
                # Получаем текущее время в UTC+7 (Дананг)
                from datetime import timedelta
                now_utc7 = datetime.utcnow() + timedelta(hours=7)
                current_time = now_utc7.time()
                
                # Проверяем: сейчас 12:00?
                if current_time.hour == 12 and current_time.minute == 0:
                    print(f"🕐 [{now_utc7.strftime('%Y-%m-%d %H:%M')}] Автоматическая публикация ассортимента...")
                    await self._auto_publish_assortment()
                    # Ждём 60 секунд чтобы не запустить дважды
                    await asyncio.sleep(60)
                
                # Ждём 60 секунд до следующей проверки
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в автопубликации: {e}")
                print(f"❌ Ошибка в автопубликации: {e}")
                await asyncio.sleep(60)
    
    async def _auto_publish_assortment(self):
        """Автоматическая публикация ассортимента"""
        try:
            print("🔄 Подготовка ассортимента...")
            
            # Подготавливаем ассортимент один раз
            final_assortment = await self._prepare_assortment()
            if not final_assortment:
                print("❌ Не удалось подготовить ассортимент")
                return
            
            # Публикуем СНАЧАЛА в Gastro форум
            print("🔄 Публикация в Gastro форум...")
            await self._publish_to_gastro_forum(final_assortment)
            
            # Потом публикуем в Shisha форум
            print("🔄 Публикация в Shisha форум...")
            await self._publish_assortment(final_assortment)
            
            print("✅ Ассортимент успешно опубликован автоматически!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка автопубликации ассортимента: {e}")
            print(f"❌ Ошибка автопубликации ассортимента: {e}")
    
    async def _publish_to_gastro_forum(self, final_assortment):
        """Публикация меню в Gastro форум"""
        try:
            print(f"📤 [GASTRO] Публикую меню...")
            
            # Используем настройки Gastro форума
            gastro_chat_id = self.config['gastro_forum_chat_id']
            gastro_thread_id = self.config['gastro_forum_thread_id']
            
            # Загружаем текст меню из JSON
            menu_file = self.config['menu_file']
            try:
                with open(menu_file, 'r', encoding='utf-8') as f:
                    menu_data = json.load(f)
                    menu_text = menu_data.get('menu_text', '')
            except Exception as e:
                print(f"❌ [GASTRO] Ошибка чтения menu.json: {e}")
                return
            
            # СНАЧАЛА удаляем ВСЕ старые сообщения
            try:
                # Получаем все сообщения из ветки
                messages = []
                async for message in self.telegram_client.iter_messages(
                    gastro_chat_id,
                    reply_to=gastro_thread_id,
                    limit=100
                ):
                    messages.append(message)
                
                print(f"🔍 [GASTRO] Найдено {len(messages)} сообщений в ветке")
                
                # Удаляем ВСЕ сообщения
                if messages:
                    print(f"🗑️ [GASTRO] Удаляю {len(messages)} старых сообщений...")
                    
                    for msg in messages:
                        try:
                            await self.telegram_client.delete_message(
                                chat_id=gastro_chat_id,
                                message_id=msg.id
                            )
                            print(f"✅ [GASTRO] Удалено сообщение ID: {msg.id}")
                        except Exception as del_error:
                            print(f"⚠️ [GASTRO] Не удалось удалить сообщение {msg.id}: {del_error}")
                else:
                    print(f"ℹ️ [GASTRO] Нет сообщений для удаления")
                
            except Exception as e:
                print(f"⚠️ [GASTRO] Ошибка удаления старых сообщений: {e}")
            
            # ПОТОМ отправляем новое меню с фотографиями
            try:
                # Получаем все фотографии из папки
                import os
                import glob
                photo_dir = 'data/picture'
                photo_files = glob.glob(os.path.join(photo_dir, '*.jpg')) + glob.glob(os.path.join(photo_dir, '*.png'))
                
                print(f"📸 [GASTRO] Найдено {len(photo_files)} фотографий: {photo_files}")
                
                # Отправляем фото с меню через Telethon
                from telethon import TelegramClient
                client = TelegramClient(self.telegram_client.session_file, self.telegram_client.api_id, self.telegram_client.api_hash)
                
                await client.start()
                entity = await client.get_entity(gastro_chat_id)
                
                if photo_files:
                    # Отправляем альбом фото с подписью
                    sent_messages = await client.send_file(
                        entity,
                        photo_files,
                        caption=menu_text,
                        reply_to=gastro_thread_id,
                        parse_mode='markdown'
                    )
                    
                    # Если отправлено несколько фото, берем ID первого
                    if isinstance(sent_messages, list):
                        new_message_id = sent_messages[0].id
                    else:
                        new_message_id = sent_messages.id
                    
                    print(f"✅ [GASTRO] Новое меню с фото опубликовано (ID: {new_message_id})")
                else:
                    # Если фото нет - отправляем только текст
                    sent_message = await client.send_message(
                        entity,
                        menu_text,
                        reply_to=gastro_thread_id,
                        parse_mode='markdown'
                    )
                    new_message_id = sent_message.id
                    print(f"✅ [GASTRO] Новое меню опубликовано без фото (ID: {new_message_id})")
                
                await client.disconnect()
                
            except Exception as send_error:
                print(f"❌ [GASTRO] Ошибка отправки меню: {send_error}")
            
            print("✅ [GASTRO] Публикация завершена")
            
        except Exception as e:
            logger.error(f"❌ [GASTRO] Ошибка публикации: {e}")
            print(f"❌ [GASTRO] Ошибка публикации: {e}")

    async def handle_publish_menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ручная публикация меню в Gastro форум (/publishmenu)"""
        try:
            await update.message.reply_text("📤 Публикую меню в Gastro форум...")
            # Подготавливаем ассортимент, чтобы структура не была пустой (не используется для меню)
            final_assortment = await self._prepare_assortment()
            await self._publish_to_gastro_forum(final_assortment or {})
            await update.message.reply_text("✅ Меню опубликовано")
        except Exception as e:
            logger.error(f"❌ Ошибка ручной публикации меню: {e}")
            await update.message.reply_text("❌ Ошибка публикации меню")
    
    def stop_auto_publish(self):
        """Остановка автопубликации"""
        self.auto_publish_running = False
        logger.info("🛑 Автопубликация остановлена")
        print("🛑 Автопубликация остановлена")
