"""
Сервис для работы с Telegram через Telethon
Подключается только когда нужно, отключается после действия
"""

import logging
import os
from telethon import TelegramClient
from telethon.tl.types import Message
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class TelegramClientService:
    """Сервис для работы с Telegram через Telethon"""
    
    def __init__(self, api_id: int, api_hash: str, session_file: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_file = session_file
    
    async def initialize(self):
        """Инициализация сервиса - проверка сессии"""
        logger.info("🔍 Проверяю Telegram сессию...")
        
        session_valid = await self.check_session_validity()
        if not session_valid:
            logger.error("❌ Telegram сессия невалидна!")
            raise Exception("Необходима валидная Telegram сессия")
        
        logger.info("✅ Telegram сессия проверена")
    
    async def send_message(self, chat_id: str, message: str, thread_id: int = None):
        """Отправка сообщения в чат/форум"""
        client = TelegramClient(self.session_file, self.api_id, self.api_hash)
        
        try:
            await client.start()
            
            if thread_id:
                # Отправка в форум с указанием thread_id
                sent_message = await client.send_message(chat_id, message, reply_to=thread_id, link_preview=False)
            else:
                # Обычная отправка в чат
                sent_message = await client.send_message(chat_id, message, link_preview=False)
                
            logger.info(f"✅ Сообщение отправлено в {chat_id}")
            return sent_message
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
            raise
        finally:
            await client.disconnect()
    
    async def get_messages(self, chat_id: str, limit: int = 100) -> List[Message]:
        """Получение последних сообщений из чата"""
        client = TelegramClient(self.session_file, self.api_id, self.api_hash)
        
        try:
            await client.start()
            
            messages = []
            async for message in client.iter_messages(chat_id, limit=limit):
                messages.append(message)
                
            logger.info(f"✅ Получено {len(messages)} сообщений из {chat_id}")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения сообщений: {e}")
            raise
        finally:
            await client.disconnect()
    
    async def get_chat_messages(self, chat_id: str, thread_id: int, limit: int = 100) -> List[Message]:
        """Получение сообщений из конкретного треда форума"""
        client = TelegramClient(self.session_file, self.api_id, self.api_hash)
        
        try:
            await client.start()
            
            messages = []
            async for message in client.iter_messages(chat_id, limit=limit):
                # Фильтруем сообщения по thread_id
                if hasattr(message, 'reply_to') and message.reply_to and message.reply_to.reply_to_msg_id == thread_id:
                    messages.append(message)
                    
            logger.info(f"✅ Получено {len(messages)} сообщений из треда {thread_id}")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения сообщений из треда: {e}")
            raise
        finally:
            await client.disconnect()
    
    async def check_session_validity(self) -> bool:
        """Проверка валидности сессии (без постоянного подключения)"""
        if not os.path.exists(self.session_file):
            logger.warning(f"❌ Файл сессии не найден: {self.session_file}")
            return False
            
        client = TelegramClient(self.session_file, self.api_id, self.api_hash)
        
        try:
            await client.start()
            
            if await client.is_user_authorized():
                me = await client.get_me()
                logger.info(f"✅ Сессия валидна! Пользователь: {me.first_name} (@{me.username})")
                return True
            else:
                logger.warning("❌ Сессия невалидна!")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки сессии: {e}")
            return False
        finally:
            await client.disconnect()

    async def get_entity(self, chat_id: str):
        """Получает информацию о чате/канале"""
        client = TelegramClient(self.session_file, self.api_id, self.api_hash)
        try:
            await client.start()
            entity = await client.get_entity(chat_id)
            logger.info(f"✅ Получена информация о {entity.title}")
            return entity
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о {chat_id}: {e}")
            raise
        finally:
            await client.disconnect()

    async def iter_messages(self, entity, reply_to=None, limit=None):
            """Итератор сообщений из чата/канала"""
            client = TelegramClient(self.session_file, self.api_id, self.api_hash)
            try:
                await client.start()
                async for message in client.iter_messages(entity, reply_to=reply_to, limit=limit):
                    yield message
            except Exception as e:
                logger.error(f"❌ Ошибка получения сообщений: {e}")
                raise
            finally:
                await client.disconnect()

    async def get_full_name(self, username: str) -> str:
            """Получает полное имя пользователя по username"""
            client = TelegramClient(self.session_file, self.api_id, self.api_hash)
            try:
                await client.start()
                user = await client.get_entity(username)
                full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                if not full_name:
                    full_name = username  # Если имя пустое, используем username
                return full_name
            except Exception as e:
                print(f"⚠️ Не удалось получить имя для {username}: {e}")
                return username  # Fallback на username
            finally:
                await client.disconnect()
    
    async def delete_message(self, chat_id: str, message_id: int):
        """Удаление сообщения"""
        client = TelegramClient(self.session_file, self.api_id, self.api_hash)
        try:
            await client.start()
            await client.delete_messages(chat_id, message_id)
            logger.info(f"✅ Сообщение {message_id} удалено из {chat_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка удаления сообщения: {e}")
            raise
        finally:
            await client.disconnect()
    
    async def get_message(self, chat_id: str, message_id: int):
        """Получение конкретного сообщения"""
        client = TelegramClient(self.session_file, self.api_id, self.api_hash)
        try:
            await client.start()
            entity = await client.get_entity(chat_id)
            # get_messages с ids возвращает один объект Message, не список
            message = await client.get_messages(entity, ids=message_id)
            return message
        except Exception as e:
            logger.error(f"❌ Ошибка получения сообщения: {e}")
            raise
        finally:
            await client.disconnect()
    
    async def edit_message(self, chat_id: str, message_id: int, text: str):
        """Редактирование сообщения"""
        client = TelegramClient(self.session_file, self.api_id, self.api_hash)
        try:
            await client.start()
            entity = await client.get_entity(chat_id)
            await client.edit_message(entity, message_id, text, parse_mode='Markdown', link_preview=False)
            logger.info(f"✅ Сообщение {message_id} отредактировано в {chat_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка редактирования сообщения: {e}")
            raise
        finally:
            await client.disconnect()