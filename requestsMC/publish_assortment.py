# Функция публикации ассортимента в чат
import json
import asyncio
from telethon import TelegramClient
from configMC import FORUM_CHAT_ID, FORUM_THREAD_ID, API_ID, API_HASH, SESSION_FILE, FLAVOR_CHANNEL, FLAVOR_THREAD_ID, DATA_DIR, IMAGES_DIR, BRAND_IMAGES

async def publish_assortment(update, context):
    """Публикация ассортимента в чат"""
    try:
        # Сначала очищаем форум (оставляем только самое старое сообщение)
        if FORUM_CHAT_ID:
            main_message_id = await clear_forum_except_oldest()
        
        # Загружаем готовый ассортимент
        final_file = "requestsMC/data/shisha/FinalAssortment.json"
        
        with open(final_file, "r", encoding="utf-8") as f:
            assortment_data = json.load(f)
        
        print(f"📤 Публикую ассортимент: {len(assortment_data)} брендов")
        
        # ДИНАМИЧЕСКИЙ СЛОВАРИК ДЛЯ ХРАНЕНИЯ ССЫЛОК НА БРЕНДЫ (только названия без грамм и цен)
        brand_links = {}
        
        
        # Отправляем каждый бренд отдельным сообщением
        for brand_name, brand_data in assortment_data.items():
            whole_packs = brand_data.get("whole_packs", [])
            loose_packs = brand_data.get("loose_packs", [])
            
            if whole_packs or loose_packs:
                # Формируем сообщение для бренда с гиперссылками
                message = format_brand_message_with_links(brand_name, whole_packs, loose_packs)
                
                # Отправляем сообщение в форум или в личный чат
                if FORUM_CHAT_ID:
                    # Отправляем в форум через Telethon (от твоего имени)
                    try:
                        sent_message, message_link = await send_to_forum_via_telethon(message, FORUM_CHAT_ID, FORUM_THREAD_ID, parse_mode='Markdown', brand_name=brand_name)
                        print(f"✅ Отправлен в форум от твоего имени: {brand_name} ({len(whole_packs) + len(loose_packs)} товаров)")
                        print(f"🔗 ССЫЛКА НА СООБЩЕНИЕ: {message_link}")
                        
                        # СОХРАНЯЕМ ССЫЛКУ В ДИНАМИЧЕСКИЙ СЛОВАРИК (название бренда как есть)
                        brand_links[brand_name] = message_link
                        
                        # Задержка между сообщениями (избегаем лимит флуда)
                        await asyncio.sleep(4)
                        
                    except Exception as forum_error:
                        print(f"❌ Ошибка отправки в форум: {forum_error}")
                        # Если не получилось в форум, отправляем в личный чат
                        await update.message.reply_text(message, parse_mode='HTML')
                        print(f"⚠️ Отправлен в личный чат вместо форума: {brand_name}")
                else:
                    # Отправляем в личный чат (как было)
                    await update.message.reply_text(message, parse_mode='HTML')
                    print(f"✅ Отправлен в личный чат бренд: {brand_name} ({len(items)} товаров)")
        
        print(f"🎉 Публикация завершена!")
        
        # ВЫВОДИМ ВСЕ СОБРАННЫЕ ССЫЛКИ
        print(f"\n📋 ДИНАМИЧЕСКИЙ СЛОВАРИК ССЫЛОК:")
        for brand, link in brand_links.items():
            print(f"   {brand}: {link}")
        
        # ТЕПЕРЬ ОБНОВЛЯЕМ ГЛАВНОЕ СООБЩЕНИЕ С ГИПЕРССЫЛКАМИ
        if FORUM_CHAT_ID and brand_links and main_message_id:
            await update_main_message_with_links(main_message_id, brand_links)
        
    except Exception as e:
        print(f"❌ Ошибка публикации ассортимента: {e}")
        await update.message.reply_text(f"❌ Ошибка публикации: {str(e)}")

def format_brand_message(brand_name, items, total_sum):
    """Форматируем сообщение для бренда"""
    
    # Жирный заголовок бренда
    message = f"**🔥 {brand_name}**\n\n"
    
    # Список товаров (простой формат)
    for item_name, quantity in items.items():
        message += f"{item_name} {quantity}\n"
    
    # Общее количество
    message += f"\n**📦 Всего: {total_sum}**"
    
    return message



def format_brand_message_with_links(brand_name, whole_packs, loose_packs):
    """Форматирование сообщения для бренда с гиперссылками на описания вкусов"""
    # Заголовок с квадратиками по бокам и жирным названием бренда заглавными буквами
    message = f"▪️▪️▪️**{brand_name.upper()}**▪️▪️▪️\n\n"
    
    # Сначала выводим целые баночки
    for flavor in whole_packs:
        name = flavor.get("name", "")
        quantity = flavor.get("quantity", 0)
        link = flavor.get("link")
        
        if link:
            # Добавляем гиперссылку
            message += f"[{name}]({link}) {quantity}\n"
        else:
            # Без гиперссылки, обычное название
            message += f"{name} {quantity}\n"
    
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
    
    # Общее количество (только целые пачки)
    total_sum = sum(flavor.get("quantity", 0) for flavor in whole_packs)
    message += f"\n**📦 Всего: {total_sum}**"
    
    return message

def find_flavor_link(brand_name, flavor_name, flavor_descriptions):
    """Ищет ссылку на описание вкуса"""
    if brand_name in flavor_descriptions:
        brand_flavors = flavor_descriptions[brand_name]
        
        # Точное совпадение
        if flavor_name in brand_flavors:
            return brand_flavors[flavor_name]
        
        # Поиск по частичному совпадению (умный поиск с учетом похожих слов)
        for desc_flavor_name, link in brand_flavors.items():
            # Нормализуем названия для сравнения
            flavor_words = set(flavor_name.lower().split())
            desc_words = set(desc_flavor_name.lower().split())
            
            # Проверяем похожие слова (для опечаток и сокращений)
            similar_words = 0
            for f_word in flavor_words:
                for d_word in desc_words:
                    if f_word == d_word:
                        similar_words += 1
            
            # Правила поиска:
            # 1. Минимум 2 слова совпадают точно ИЛИ похоже
            # 2. ИЛИ 1 слово совпадает точно ИЛИ похоже + короткое название
            if similar_words >= 2 or (similar_words >= 1 and len(flavor_words) <= 2):
                return link
            
    return None

def format_item_line(item_name, quantity):
    """Форматируем строку товара с выравниванием"""
    
    # Максимальная длина строки (уменьшено для Telegram)
    max_length = 25
    
    # Преобразуем количество в строку
    qty_str = str(quantity)
    
    # Рассчитываем сколько места занимает название
    name_max_length = max_length - len(qty_str)
    
    # Обрезаем название если оно слишком длинное
    if len(item_name) > name_max_length:
        item_name = item_name[:name_max_length-3] + "..."
    
    # Рассчитываем количество точек для заполнения
    dots_count = max_length - len(item_name) - len(qty_str)
    
    # Создаем строку с выравниванием (чередование пробел-средняя точка)
    filler = ""
    for i in range(max(1, dots_count)):
        if i % 2 == 0:
            filler += " "
        else:
            filler += "·"
    
    return f"{item_name}{filler}{qty_str}"

async def clear_forum_except_oldest():
    """Очищает форум, оставляя только самое старое сообщение"""
    # API ключи для Telethon (рабочий аккаунт)
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    
    await client.start()
    
    try:
        # Получаем информацию о канале
        entity = await client.get_entity(FORUM_CHAT_ID)
        print(f"🔍 Очищаю форум: {entity.title}")
        
        # Получаем все сообщения в ветке
        messages = []
        async for message in client.iter_messages(entity, reply_to=FORUM_THREAD_ID, limit=None):
            messages.append(message)
        
        # ПОКАЗЫВАЕМ ВСЕ СООБЩЕНИЯ ДЛЯ ОТЛАДКИ
        print(f"📋 ВСЕ СООБЩЕНИЯ В ФОРУМЕ ({len(messages)} шт.):")
        for i, message in enumerate(messages):
            text_preview = message.text[:50] if message.text else "Нет текста"
            print(f"   {i}: ID {message.id} | Дата: {message.date} | Текст: {text_preview}...")
        
        if len(messages) <= 1:
            print("✅ В форуме только одно сообщение, очистка не нужна")
            return
        
        # Находим главное сообщение (с текстом, самое старое)
        main_messages = [m for m in messages if m.text and len(m.text) > 10]
        if not main_messages:
            print("❌ Не найдено главное сообщение с текстом!")
            return
        
        main_message = min(main_messages, key=lambda m: m.date)
        print(f"📌 Главное сообщение: ID {main_message.id} | Дата: {main_message.date}")
        print(f"📌 Всего сообщений: {len(messages)}")
        
        # Удаляем все сообщения кроме главного
        deleted_count = 0
        for message in messages:
            if message.id == main_message.id:  # Пропускаем главное сообщение
                print(f"⏭️ Пропускаем главное сообщение ID {message.id}")
                continue
            
            try:
                await client.delete_messages(entity, message.id)
                deleted_count += 1
                print(f"🗑️ Удалено сообщение ID {message.id}")
            except Exception as e:
                print(f"❌ Не удалось удалить сообщение ID {message.id}: {e}")
        
        print(f"✅ Очистка завершена! Удалено {deleted_count} сообщений")
        
        # Возвращаем ID главного сообщения
        return main_message.id
        
    except Exception as e:
        print(f"❌ Ошибка очистки форума: {e}")
        return None
    
    finally:
        await client.disconnect()

async def update_assortment(update, context):
    """Обновляет содержимое существующих сообщений с ассортиментом (после отгрузки)"""
    try:
        print("🔄 Начинаю обновление ассортимента...")
        
        # Загружаем финальный ассортимент (должен быть уже обновлен)
        assortment_file = "requestsMC/data/shisha/FinalAssortment.json"
        try:
            with open(assortment_file, "r", encoding="utf-8") as f:
                assortment_data = json.load(f)
            print(f"📦 Загружен СВЕЖИЙ ассортимент: {len(assortment_data)} брендов")
        except FileNotFoundError:
            print("❌ Файл ассортимента не найден!")
            return
        
        # Загружаем описания вкусов с ссылками
        flavor_descriptions_file = "requestsMC/data/shisha/FlavorDescriptions.json"
        flavor_descriptions = {}
        try:
            with open(flavor_descriptions_file, "r", encoding="utf-8") as f:
                flavor_descriptions = json.load(f)
            print(f"📚 Загружены описания вкусов: {len(flavor_descriptions)} брендов")
        except FileNotFoundError:
            print("⚠️ Файл описаний вкусов не найден, гиперссылки не будут добавлены")
        
        # Используем конфиг
        client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
        await client.start()
        
        try:
            # Получаем entity для форума
            entity = await client.get_entity(FORUM_CHAT_ID)
            print(f"🔍 Подключился к форуму: {entity.title}")
            
            # Получаем все сообщения в форуме
            messages = []
            async for message in client.iter_messages(entity, reply_to=FORUM_THREAD_ID, limit=None):
                if message.text:  # Только сообщения с текстом
                    messages.append(message)
            
            print(f"📋 Найдено {len(messages)} сообщений в форуме")
            
            # Сортируем сообщения по дате (от старых к новым)
            messages.sort(key=lambda x: x.date)
            
            # Пропускаем первое сообщение (главное) - оно не изменяется
            brand_messages = messages[1:]  # Сообщения с брендами
            
            print(f"📝 Будем обновлять {len(brand_messages)} сообщений с брендами")
            
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
                    new_message = format_brand_message_with_links(brand_name, whole_packs, loose_packs)
                    
                    # Получаем сообщение для обновления
                    message_to_update = brand_messages[i]
                    
                    # Показываем детали изменений
                    whole_packs_count = len(whole_packs)
                    loose_packs_count = len(loose_packs)
                    
                    print(f"📝 ДЕТАЛИ ИЗМЕНЕНИЙ для {brand_name}:")
                    print(f"   Целые пачки: {whole_packs_count} товаров")
                    print(f"   Наразвес: {loose_packs_count} товаров")
                    
                    try:
                        # Обновляем сообщение
                        await client.edit_message(
                            entity=entity,
                            message=message_to_update,
                            text=new_message,
                            parse_mode='Markdown',
                            link_preview=False
                        )
                        
                        print(f"✅ Обновлено сообщение {i+1}: {brand_name} ({whole_packs_count + loose_packs_count} товаров)")
                        
                        # Отправляем уведомление в чат об обновлении
                        try:
                            await update.effective_chat.send_message(f"✅ Обновил ассортимент {brand_name}")
                        except Exception as chat_error:
                            print(f"⚠️ Не удалось отправить уведомление в чат: {chat_error}")
                        
                        # Задержка между обновлениями (избегаем лимит флуда Telegram)
                        await asyncio.sleep(5)
                        
                    except Exception as e:
                        error_msg = str(e)
                        if "Content of the message was not modified" in error_msg:
                            print(f"ℹ️ Сообщение {i+1}: {brand_name} - без изменений")
                        else:
                            print(f"❌ Ошибка обновления сообщения {i+1}: {e}")
            
            print("🎉 Обновление ассортимента завершено!")
            
        except Exception as e:
            print(f"❌ Ошибка обновления: {e}")
        
        finally:
            await client.disconnect()
    
    except Exception as e:
        print(f"❌ Критическая ошибка обновления ассортимента: {e}")

async def send_to_forum_via_telethon(message, chat_id, thread_id=None, parse_mode='Markdown', brand_name=None):
    """Отправка сообщения в форум через Telethon"""
    # Используем существующую сессию из конфига
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    
    await client.start()
    
    try:
        # Получаем entity для создания ссылок
        entity = await client.get_entity(chat_id)
        chat_id_numeric = entity.id
        
        # Проверяем есть ли фото для бренда
        image_path = None
        if brand_name and brand_name in BRAND_IMAGES:
            image_path = f"{IMAGES_DIR}{BRAND_IMAGES[brand_name]}"
            import os
            if not os.path.exists(image_path):
                image_path = None  # Файл не найден, отправляем без фото
        
        # Отправляем сообщение в форум
        if thread_id:
            # Отправляем в конкретную ветку
            # Проверяем длину сообщения - если слишком длинное, отправляем без фото
            # Отправляем без фото, только текст
            sent_message = await client.send_message(
                entity=chat_id,
                message=message,
                reply_to=thread_id,
                parse_mode=parse_mode,
                link_preview=False
            )
        else:
            # Отправляем в общий чат без фото
            sent_message = await client.send_message(
                entity=chat_id,
                message=message,
                parse_mode=parse_mode,
                link_preview=False
            )
        
        # Создаем ссылку на сообщение
        message_link = f"https://t.me/c/{chat_id_numeric}/{sent_message.id}"
        print(f"🔗 Ссылка на сообщение: {message_link}")
        
        return sent_message, message_link
        
    finally:
        await client.disconnect()

async def update_main_message_with_links(main_message_id, brand_links):
    """Обновляет главное сообщение, добавляя гиперссылки к названиям брендов"""
    # API ключи для Telethon (рабочий аккаунт)
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    
    await client.start()
    
    try:
        # Получаем entity канала
        entity = await client.get_entity(FORUM_CHAT_ID)
        
        # Получаем главное сообщение
        main_message = await client.get_messages(entity, ids=main_message_id)
        if not main_message:
            print(f"❌ Не удалось получить главное сообщение ID {main_message_id}")
            return
        
        current_text = main_message.text
        print(f"📝 Текущий текст главного сообщения: {current_text[:100]}...")
        
        # СНАЧАЛА УДАЛЯЕМ ВСЕ СТАРЫЕ ГИПЕРССЫЛКИ
        import re
        updated_text = current_text
        
        # СНАЧАЛА удаляем жирный текст **
        updated_text = re.sub(r'\*\*', '', updated_text)
        print("🧹 Удален жирный текст **")
        
        # ПОТОМ удаляем все гиперссылки в формате [текст](ссылка)
        updated_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', updated_text)
        print("🧹 Удалены все старые гиперссылки")
        
        # ТЕПЕРЬ ДОБАВЛЯЕМ НОВЫЕ ГИПЕРССЫЛКИ
        # ВАЖНО: Сначала длинные названия, потом короткие!
        
        # Сортируем по длине названия (от длинного к короткому)
        sorted_brands = sorted(brand_links.items(), key=lambda x: len(x[0]), reverse=True)
        
        for brand_name, link in sorted_brands:
            # Создаем гиперссылку в формате Markdown
            hyperlink = f"[{brand_name}]({link})"
            
            # Ищем только название бренда
            search_pattern = brand_name
            replace_pattern = hyperlink
            
            # Заменяем в тексте
            if search_pattern in updated_text:
                updated_text = updated_text.replace(search_pattern, replace_pattern)
                print(f"🔗 Заменено '{search_pattern}' на гиперссылку")
            else:
                print(f"⚠️ Не найдено '{search_pattern}' в тексте")
        
        # ВОССТАНАВЛИВАЕМ жирный текст в начале и конце
        if not updated_text.startswith('**'):
            updated_text = '**' + updated_text
        if not updated_text.endswith('**'):
            updated_text = updated_text + '**'
        
        # Отправляем обновленное сообщение
        await client.edit_message(entity, main_message_id, updated_text, parse_mode='Markdown')
        print(f"✅ Главное сообщение обновлено с гиперссылками!")
        
    except Exception as e:
        print(f"❌ Ошибка обновления главного сообщения: {e}")
    
    finally:
        await client.disconnect()
