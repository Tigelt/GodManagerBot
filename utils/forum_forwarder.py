#!/usr/bin/env python3
"""
Скрипт для пересылки сообщений между ветками форума
"""

import asyncio
import time
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.messages import ForwardMessagesRequest
from telethon.tl.types import InputPeerChannel
import logging

# Загружаем переменные окружения
load_dotenv()

# Убираем логи, используем принты

class ForumForwarder:
    def __init__(self, session_name, api_id, api_hash):
        self.client = TelegramClient(session_name, api_id, api_hash)
        
    async def start(self):
        """Запуск клиента"""
        await self.client.start()
        print("✅ Клиент запущен")
        
    async def stop(self):
        """Остановка клиента"""
        await self.client.disconnect()
        print("❌ Клиент остановлен")
        
    async def get_chat_info(self, chat_id):
        """Получение информации о чате"""
        try:
            entity = await self.client.get_entity(chat_id)
            print(f"📋 Чат: {entity.title} (ID: {chat_id})")
            return entity
        except Exception as e:
            print(f"❌ Ошибка получения информации о чате {chat_id}: {e}")
            return None
        
    async def forward_messages(self, source_forum_link, source_topic_id, target_forum_link, target_topic_id, delay=1):
        """
        Пересылка сообщений между ветками форума
        
        Args:
            source_forum_link: Ссылка на исходный форум
            source_topic_id: ID ветки в исходном форуме
            target_forum_link: Ссылка на целевой форум
            target_topic_id: ID ветки в целевом форуме
            delay: Задержка между пересылками в секундах
        """
        try:
            print(f"🔄 Начинаю пересылку сообщений из {source_forum_link} ветка {source_topic_id} в {target_forum_link} ветка {target_topic_id}")
            
            # Получаем сущности форумов
            print("📋 Получаю сущности форумов...")
            source_entity = await self.client.get_entity(source_forum_link)
            target_entity = await self.client.get_entity(target_forum_link)
            
            print(f"📋 Исходный форум: {source_entity.title}")
            print(f"📋 Целевой форум: {target_entity.title}")
            
            # Получаем сообщения из конкретной ветки форума
            print(f"🔍 Получаю сообщения из ветки {source_topic_id}...")
            messages = []
            async for message in self.client.iter_messages(
                source_entity, 
                reply_to=source_topic_id,
                limit=None
            ):
                messages.append(message)
            
            print(f"🔍 Найдено {len(messages)} сообщений в ветке {source_topic_id}")
            
            if not messages:
                print("❌ Сообщения не найдены в ветке")
                print("🔍 Попробуем получить все сообщения из форума для отладки...")
                all_messages = []
                async for msg in self.client.iter_messages(source_entity, limit=10):
                    all_messages.append(msg)
                print(f"📋 Всего сообщений в форуме: {len(all_messages)}")
                for i, msg in enumerate(all_messages):
                    print(f"   {i+1}: ID {msg.id}, reply_to: {getattr(msg.reply_to, 'reply_to_msg_id', 'None') if hasattr(msg, 'reply_to') and msg.reply_to else 'None'}")
                return
                
            print(f"📨 Найдено {len(messages)} сообщений для пересылки")
            
            # Пересылаем каждое сообщение
            print(f"🚀 Начинаю пересылку {len(messages)} сообщений...")
            for i, message in enumerate(messages, 1):
                print(f"📤 Обрабатываю сообщение {i}/{len(messages)}...")
                try:
                    # Отправляем текст сообщения в указанную ветку форума
                    if message.text:
                        print(f"📝 Отправляю текст: {message.text[:50]}...")
                        await self.client.send_message(
                            entity=target_entity,  # Сущность форума
                            message=message.text,
                            reply_to=target_topic_id  # ID ветки (исправлено!)
                        )
                    else:
                        # Если нет текста, отправляем уведомление
                        print("📝 Отправляю уведомление о сообщении без текста...")
                        await self.client.send_message(
                            entity=target_entity,  # Сущность форума
                            message="[Пересланное сообщение без текста]",
                            reply_to=target_topic_id  # ID ветки (исправлено!)
                        )
                    print(f"✅ Переслано сообщение {i}/{len(messages)}")
                    
                    # Задержка между пересылками
                    if i < len(messages):  # Не ждем после последнего сообщения
                        print(f"⏳ Жду {delay} секунд...")
                        await asyncio.sleep(delay)
                        
                except Exception as e:
                    print(f"❌ Ошибка при пересылке сообщения {i}: {e}")
                    print(f"🔍 Тип ошибки: {type(e).__name__}")
                    continue
                    
            print("🎉 Пересылка завершена!")
            
        except Exception as e:
            print(f"❌ Ошибка пересылки: {e}")

async def main():
    """Основная функция"""
    import sys
    
    # Настройки из .env файла
    SESSION_NAME = 'botAccount'  # Имя сессии
    API_ID = int(os.getenv('TELEGRAM_API_ID'))
    API_HASH = os.getenv('TELEGRAM_API_HASH')
    
    # Параметры форума - ЗАПОЛНИ САМ
    SOURCE_FORUM_LINK = "@gogoelis"  # Ссылка на форум где лежат сообщения
    SOURCE_TOPIC_ID = 831  # ID ветки в исходном форуме (откуда пересылать)
    TARGET_FORUM_LINK = "@shiflael"  # Ссылка на целевой форум
    TARGET_TOPIC_ID = 2 # ID ветки в целевом форуме (куда пересылать)
    
    # Создаем экземпляр пересыльщика
    forwarder = ForumForwarder(SESSION_NAME, API_ID, API_HASH)
    
    try:
        # Запускаем клиент
        await forwarder.start()
        
        # Пересылаем сообщения
        await forwarder.forward_messages(
            source_forum_link=SOURCE_FORUM_LINK,
            source_topic_id=SOURCE_TOPIC_ID,
            target_forum_link=TARGET_FORUM_LINK,
            target_topic_id=TARGET_TOPIC_ID,
            delay=1   # Задержка 1 секунда
        )
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        # Останавливаем клиент
        await forwarder.stop()

if __name__ == "__main__":
    print("🚀 Запуск пересыльщика сообщений...")
    asyncio.run(main())
