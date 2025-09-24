import asyncio
import json
import re
from telethon import TelegramClient
from configMC import FLAVOR_CHANNEL, API_ID, API_HASH, SESSION_FILE, DATA_DIR, FLAVOR_THREAD_ID, ACTUAL_BRANDS

async def update_base_flavor_descriptions(update, context):
    """Обновляет JSON файл с описаниями вкусов из ветки 16"""
    try:
        print("🔄 Начинаю обновление описаний вкусов...")
        
        # API ключи для Telethon (рабочий аккаунт)
        client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
        await client.start()
        
        try:
            # Получаем информацию о канале с описаниями
            entity = await client.get_entity(FLAVOR_CHANNEL)
            print(f"🔍 Парсю ветку с описаниями: {entity.title} (Thread ID: {FLAVOR_THREAD_ID})")
            
            # Получаем все сообщения в ветке с описаниями
            messages = []
            async for message in client.iter_messages(entity, reply_to=FLAVOR_THREAD_ID, limit=None):
                if message.text:  # Только сообщения с текстом
                    messages.append(message)
            
            print(f"📋 Найдено {len(messages)} сообщений с описаниями")
            
            # Создаем структуру для хранения описаний вкусов
            flavor_descriptions = {}
            
            # Идем по массиву актуальных брендов
            for brand in ACTUAL_BRANDS:
                print(f"🔍 Ищу сообщения для бренда: {brand}")
                
                # Создаем хештег для поиска (в нижнем регистре)
                hashtag = f"#{brand.lower().replace(' ', '')}"
                
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
                        # Берем первую строку как название вкуса
                        lines = message.text.strip().split('\n')
                        if lines:
                            flavor_name = lines[0].strip()
                            
                            # Создаем ссылку на сообщение
                            message_link = f"https://t.me/{entity.username}/{message.id}"
                            
                            # Добавляем в структуру
                            flavor_descriptions[brand][flavor_name] = message_link
                            print(f"  ✅ {flavor_name} → {message_link}")
                
                # Если не нашли сообщения для бренда, создаем пустую секцию
                if brand not in flavor_descriptions:
                    flavor_descriptions[brand] = {}
                    print(f"  ⚠️ Не найдено сообщений для {brand}")
            
            # Добавляем секцию "Остальные" для сообщений без хештегов брендов
            print("🔍 Ищу сообщения без хештегов брендов...")
            other_messages = []
            brand_hashtags = [f"#{brand.lower().replace(' ', '')}" for brand in ACTUAL_BRANDS]
            
            for message in messages:
                if message.text:
                    # Проверяем, есть ли в сообщении хештеги брендов
                    has_brand_hashtag = any(hashtag in message.text.lower() for hashtag in brand_hashtags)
                    if not has_brand_hashtag:
                        other_messages.append(message)
            
            if other_messages:
                flavor_descriptions["Остальные"] = {}
                for i, message in enumerate(other_messages[:20]):  # Первые 20 сообщений
                    # Берем первые 20 символов как название
                    flavor_name = message.text[:20].strip()
                    message_link = f"https://t.me/{entity.username}/{message.id}"
                    flavor_descriptions["Остальные"][flavor_name] = message_link
                    print(f"  ✅ {flavor_name} → {message_link}")
            
            print(f"📊 Всего обработано брендов: {len(flavor_descriptions)}")
            
            # Сохраняем результат в JSON файл
            output_file = f"{DATA_DIR}FlavorDescriptions.json"
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
            
            await update.effective_chat.send_message(result_message)
            
        except Exception as e:
            print(f"❌ Ошибка парсинга: {e}")
            await update.effective_chat.send_message(f"❌ Ошибка обновления описаний: {str(e)}")
        
        finally:
            await client.disconnect()
            
    except Exception as e:
        print(f"❌ Ошибка обновления описаний вкусов: {e}")
        await update.effective_chat.send_message(f"❌ Ошибка: {str(e)}")