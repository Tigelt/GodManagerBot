#!/usr/bin/env python3
"""
Главный файл запуска GodManagerBot v2.0
"""

import asyncio
import logging
from dotenv import load_dotenv
from core.bot import GodManagerBot
from config.settings import load_config

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования - только ERROR и выше
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Главная функция запуска"""
    try:
        print("🚀 Запуск GodManagerBot v2.0...")
        
        # Загружаем конфигурацию
        config = load_config()
        print("✅ Конфигурация загружена")
        
        # Создаем и запускаем бота
        bot = GodManagerBot(config)
        bot.start()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")
        raise

if __name__ == "__main__":
    main()
