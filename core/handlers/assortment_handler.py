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
            final_assortment = await self._prepare_assortment2()
            if not final_assortment:
                await update.message.reply_text("❌ Не удалось подготовить ассортимент")
                return
            
            await update.message.reply_text("🔄 Публикую ассортимент, пожалуйста ожидайте...")
            
            # Публикуем ассортимент
            #await self._publish_assortment(final_assortment, update, context)
            await self._publish_assortment2(update, context)
            
            await update.message.reply_text("✅ Ассортимент успешно добавлен!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки команды /assortment: {e}")
            await update.message.reply_text("❌ Ошибка публикации ассортимента")
    
    async def handle_update_assortment_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /updateassortment"""
        try:
            await update.message.reply_text("🔄 Обновляю ассортимент...")
            
            # Сначала обновляем данные из Мой Склад
            #await self._prepare_assortment()
            await self._prepare_assortment2()
            
            # Потом обновляем сообщения в форуме
            await self._update_assortment2()
            
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
    
    async def handle_inventory_command3(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /inventory - показывает инвентарь табаков"""
        try:
            await update.message.reply_text("🔄 Загружаю инвентарь...")
            
            # Подготавливаем ассортимент (как в _publish_assortment)
            final_assortment = await self._prepare_assortment2()
            
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
            
            
            
    async def handle_inventory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await update.message.reply_text("🔄 Загружаю инвентарь...")

            # 1. Обновляем файл
            await self._prepare_assortment2()

            # 2. Читаем файл
            with open("data/finalAssortment.json", "r", encoding="utf-8") as f:
                final_assortment = json.load(f)

            # 3. Отправляем
            for brand_name, brand_data in final_assortment.items():
                whole_packs = brand_data["whole_packs"]["flavour"]
                loose_packs = brand_data["loose_packs"]["flavour"]

                if not whole_packs and not loose_packs:
                    continue

                message = self._format_brand_message2(
                    brand_name,
                    whole_packs,
                    loose_packs
                )

                await update.message.reply_text(message)
                await asyncio.sleep(1)

            await update.message.reply_text("✅ Инвентарь загружен!")

        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            await update.message.reply_text("❌ Ошибка загрузки инвентаря")
            
            
            
            
            
            
            
            
            
            
            
            
            
    def final_assortment2(self):
        # Загружаем маленький файл с брендами
        with open("data/brand.json", "r", encoding="utf-8") as f:
            brands = json.load(f)

        # Загружаем большой файл с остатками
        with open("data/StockData2.json", "r", encoding="utf-8") as f:
            stock_data = json.load(f)

        # Проходим по каждому объекту маленького файла
        for brand_key, brand_info in brands.items():
            brand_name = brand_info["name"]

            # Проходим по каждому объекту большого файла
            for item in stock_data:
                item_name = item["name"]
                item_stock = item["stock"] - item["reserve"]
                if item_stock <= 0:
                    continue

                # Сравниваем название бренда
                if brand_name in item_name:
                    # Получаем "чистое" имя вкуса без бренда и веса
                    flavour_name = item_name
                    if flavour_name.startswith(brand_name):
                        flavour_name = flavour_name[len(brand_name):].strip()

                    # Убираем вес в конце
                    if flavour_name.endswith(brand_info["whole_packs"]["weight"]):
                        flavour_name = flavour_name[:-len(brand_info["whole_packs"]["weight"])].strip()
                    elif flavour_name.endswith(brand_info["loose_packs"]["weight"]):
                        flavour_name = flavour_name[:-len(brand_info["loose_packs"]["weight"])].strip()

                    # Проверяем whole packs
                    if brand_info["whole_packs"]["weight"] in item_name:
                        brand_info["whole_packs"]["flavour"].append({
                            "name": flavour_name,
                            "stock": item_stock
                        })
                    # Проверяем loose packs
                    elif brand_info["loose_packs"]["weight"] in item_name:
                        brand_info["loose_packs"]["flavour"].append({
                            "name": flavour_name,
                            "stock": item_stock
                        })

        # Сохраняем результат в файл
        with open("data/finalAssortment.json", "w", encoding="utf-8") as f:
            for brand_info in brands.values():
                # сортировка целых
                brand_info["whole_packs"]["flavour"].sort(
                key=lambda x: x["name"].lower()
                )

                # сортировка вскрытых
                brand_info["loose_packs"]["flavour"].sort(
                key=lambda x: x["name"].lower()
                )
            json.dump(brands, f, ensure_ascii=False, indent=4)

        return brands
    async def _prepare_assortment2(self):
        """Подготавливает ассортимент - тянет остатки со склада и создает FinalAssortment"""
        try:
            print("🔄 Начинаю подготовку ассортиментаffff...")
            
            # Получаем остатки со склада
            
            stock_data = await self._get_stock_data2()
            gg = self.final_assortment2()
            if not stock_data:
                print("❌ Не удалось получить остатки")
            return 1
        except Exception as e:
            logger.error(f"❌ Ошибка подготовки ассортимента: {e}")
            return None
        
    async def _get_stock_data2(self):
        """Получает актуальный ассортимент асинхронно"""
        try:
            logger.info("🔄 Получаю ассортимент...")

            # МЕНЯЕМ ТОЛЬКО URL
            url = "https://api.moysklad.ru/api/remap/1.2/entity/assortment"

            # МЕНЯЕМ ТОЛЬКО ПАРАМЕТРЫ
            params = {
                "filter": "type=variant;stockMode=positiveonly",
                "expand": "product,product.productFolder",
                "limit": 1000
            }

            # ВОТ ОНИ — ТВОИ СТРОКИ (НИКУДА НЕ ДЕЛИСЬ)
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.config["moy_sklad_token"]}',
                    'Content-Type': 'application/json'
                }

                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        cleaned = []
                        for item in data.get("rows", []):
                            cleaned.append({
                                "name": item.get("name"),
                                "stock": item.get("stock"),
                                "reserve": item.get("reserve"),
                                "inTransit": item.get("inTransit"),
                                "quantity": item.get("quantity"),
                            })

                        stock_file = self.config['stock_data_file2']
                        with open(stock_file, "w", encoding="utf-8") as f:
                            json.dump(cleaned, f, ensure_ascii=False, indent=2)
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка API: {response.status} - {error_text}")
                    return None

        except Exception as e:
            logger.error(f"❌ Ошибка получения ассортимента: {e}")
        return None
    
    def format_name(self, name):
        if "(" in name:
            main, rest = name.split("(", 1)
            return f"**{main.strip()}** ({rest}"
        return f"**{name}**"
    
    def _format_brand_message2(self, brand_name, whole_packs, loose_packs):
        """Форматирование сообщения для бренда"""

        # Заголовок
        message = f"▪️**{brand_name.upper()}**▪️\n\n"

        # Целые банки
        for flavor in whole_packs:
            raw_name = flavor.get("name", "")
            name = self.format_name(raw_name)
            quantity = int(flavor.get("stock", 0))
            link = flavor.get("link")

            display_quantity = "3+" if quantity > 3 else str(quantity)

            if link:
                message += f"[{name}]({link}) {display_quantity}\n"
            else:
                message += f"{name} {display_quantity}\n"

        # Вскрытые
        if loose_packs:
            message += "\n---\n**Вскрытые вкусы:**\n"

            for flavor in loose_packs:
                raw_name = flavor.get("name", "")
                name = self.format_name(raw_name)
                raw_quantity = flavor.get("stock", 0)
                quantity = int(raw_quantity // 25 * 25)
                link = flavor.get("link")

                # ФИЛЬТР
                if quantity < 30:
                    continue
                if link:
                    message += f"[{name}]({link}) {quantity}г\n"
                else:
                    message += f"{name} {quantity}г\n"

        return message
    
    
    async def _publish_assortment2(self, update=None, context=None):
        try:
            # Загружаем финальный ассортимент
            with open("data/finalAssortment.json", "r", encoding="utf-8") as f:
                final_assortment = json.load(f)

            print(f"📤 Публикую ассортимент: {len(final_assortment)} брендов")

            main_message_id = await self._clear_forum_except_oldest()
            brand_links = {}

            for brand_name, brand_data in final_assortment.items():

                whole_packs = brand_data.get("whole_packs", {}).get("flavour", [])
                loose_packs = brand_data.get("loose_packs", {}).get("flavour", [])

                if whole_packs or loose_packs:
                    message = self._format_brand_message2(
                        brand_name,
                        whole_packs,
                        loose_packs
                    )

                    try:
                        sent_message = await self.telegram_client.send_message(
                            chat_id=self.config['forum_chat_id'],
                            message=message,
                            thread_id=self.config['forum_thread_id']
                        )

                        entity = await self.telegram_client.get_entity(self.config['forum_chat_id'])
                        chat_id_numeric = entity.id
                        message_link = f"https://t.me/c/{chat_id_numeric}/{sent_message.id}"
                        brand_links[brand_name] = message_link

                        import asyncio
                        await asyncio.sleep(4)

                    except Exception as forum_error:
                        print(f"❌ Ошибка отправки: {forum_error}")

            if self.config['forum_chat_id'] and brand_links and main_message_id:
                await self._update_main_message_with_links(main_message_id, brand_links)

            print("🎉 Публикация завершена!")

        except Exception as e:
            print(f"❌ Ошибка публикации ассортимента: {e}")
            raise e
    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    
 
    
   
    
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
    
    
            
            
            
            
    async def _update_assortment2(self):
        try:
            print("🔄 Обновляю ассортимент...")

            # 1. Загружаем финальный ассортимент
            with open("data/finalAssortment.json", "r", encoding="utf-8") as f:
                assortment_data = json.load(f)

            # 2. Получаем сообщения из форума
            messages = []
            async for message in self.telegram_client.iter_messages(
                self.config['forum_chat_id'],
                reply_to=self.config['forum_thread_id'],
                limit=None
            ):
                if message.text:
                    messages.append(message)

            # 3. Сортируем по дате (старые → новые)
            messages.sort(key=lambda x: x.date)

            # 4. Убираем главное сообщение
            brand_messages = messages[1:]

            # 5. Обновляем по порядку
            for i, (brand_name, brand_data) in enumerate(assortment_data.items()):
                if i >= len(brand_messages):
                    break

                whole_packs = brand_data["whole_packs"]["flavour"]
                loose_packs = brand_data["loose_packs"]["flavour"]

                # пропускаем пустые
                if not whole_packs and not loose_packs:
                    continue

                new_text = self._format_brand_message2(
                    brand_name,
                    whole_packs,
                    loose_packs
                )

                message_to_update = brand_messages[i]

                try:
                    await self.telegram_client.edit_message(
                        chat_id=self.config['forum_chat_id'],
                        message_id=message_to_update.id,
                        text=new_text
                    )

                    print(f"✅ {brand_name} обновлён")

                except Exception as e:
                    if "not modified" in str(e):
                        print(f"ℹ️ {brand_name} без изменений")
                    else:
                        print(f"❌ Ошибка {brand_name}: {e}")

        except Exception as e:
            print(f"❌ Общая ошибка: {e}")     
            
            
            
            
            
            
            
            
            
            
            
            
    
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
            from datetime import timedelta
            now_utc7 = datetime.utcnow() + timedelta(hours=7)
            weekday = now_utc7.weekday()  # Пн=0 ... Вс=6
            print(f"🗓️ [AUTO] Текущее время (UTC+7): {now_utc7.strftime('%Y-%m-%d %H:%M')}, weekday={weekday}")

            # Публикация меню Gastro (кроме воскресенья)
            if weekday == 6:
                print("⏭️ [AUTO] Воскресенье — меню Gastro не публикуем")
            else:
                print("🔄 [AUTO] Публикация меню в Gastro форум")
                await self._publish_to_gastro_forum()

            # Публикация ассортимента Shisha (кроме среды)
            if weekday == 2:
                print("⏭️ [AUTO] Среда — ассортимент Shisha не публикуем")
            else:
                print("🔄 [AUTO] Подготавливаю ассортимент Shisha...")
                final_assortment = await self._prepare_assortment()
                if not final_assortment:
                    print("❌ [AUTO] Не удалось подготовить ассортимент Shisha")
                    return

                print("🔄 [AUTO] Публикация ассортимента Shisha...")
                await self._publish_assortment(final_assortment)
                print("✅ [AUTO] Ассортимент Shisha опубликован")

            print("✅ [AUTO] Автопубликация завершена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка автопубликации ассортимента: {e}")
            print(f"❌ Ошибка автопубликации ассортимента: {e}")
    
   