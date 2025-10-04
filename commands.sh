#!/bin/bash
# Команды для управления GodManagerBot

prepare_bot() {
    echo "🚀 Подготовка GodManagerBot..."
    
    echo "🔐 Шаг 1: Создание сессии Telegram..."
    python3 utils/auth.py
    
    echo "📦 Шаг 2: Обновление списка товаров..."
    python3 -c "
import asyncio
import sys
import os
sys.path.append('.')
from services.moy_sklad import MoySkladAPI
from config.settings import load_config

async def main():
    config = load_config()
    api = MoySkladAPI(config['moy_sklad_token'], config)
    await api._save_all_items_to_json('data/ItemNameHref.json')
    print('✅ Товары обновлены')

asyncio.run(main())
"
    
    echo "✅ Подготовка завершена!"
    echo "📋 Теперь можно запустить: ./commands.sh start"
}

start() {
    echo "🚀 Запуск GodManagerBot..."
    docker-compose up --build
}

rebuild() {
    echo "🔧 Пересборка GodManagerBot..."
    docker-compose down
    docker-compose up --build
}

push() {
    echo "📤 Отправка изменений в GitHub..."
    
    echo "📋 Проверяем статус Git..."
    git status
    
    echo "📦 Добавляем все изменения..."
    git add .
    
    echo "💾 Создаем commit..."
    git commit -m "Update: $(date '+%Y-%m-%d %H:%M:%S')"
    
    echo "🚀 Отправляем в GitHub..."
    git push
    
    echo "✅ Изменения отправлены в GitHub!"
}

# Проверяем аргумент
case "$1" in
    "prepare_bot")
        prepare_bot
        ;;
    "start")
        start
        ;;
    "rebuild")
        rebuild
        ;;
    "push")
        push
        ;;
    *)
        echo "❌ Неизвестная команда: $1"
        echo "📋 Доступные команды:"
        echo "  prepare_bot - подготовка бота"
        echo "  start - запуск бота"
        echo "  rebuild - пересборка и запуск"
        echo "  push - отправить изменения в GitHub"
        exit 1
        ;;
esac