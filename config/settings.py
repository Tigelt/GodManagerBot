"""
Конфигурация GodManagerBot v2.0
"""

import os
import json
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """Загрузка конфигурации"""
    return {
        # Telegram Bot
        'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
        
        # Telegram API (для Telethon)
        'telegram_api_id': int(os.getenv('TELEGRAM_API_ID', '0')),
        'telegram_api_hash': os.getenv('TELEGRAM_API_HASH', ''),
        'session_file': 'botAccount.session',
        
        # Мой Склад
        'moy_sklad_token': os.getenv('MOY_SKLAD_TOKEN', ''),
        'organization_href': os.getenv('ORGANIZATION_HREF', ''),
        'store_href': os.getenv('STORE_HREF', ''),
        
        # Google Sheets
        'google_sheets_key_base64': os.getenv('GOOGLE_SHEETS_KEY_BASE64', ''),
        'spreadsheet_id': os.getenv('SPREADSHEET_ID', ''),
        'shisha_worksheet_name': os.getenv('SHISHA_WORKSHEET_NAME', 'Shisha'),
        'gastro_worksheet_name': os.getenv('GASTRO_WORKSHEET_NAME', 'Gastro'),
        'gastro_inventory_worksheet_name': os.getenv('GASTRO_INVENTORY_WORKSHEET_NAME', 'ПРОДУКТЫ'),
        
        # Пользователи
        'shisha_username': os.getenv('SHISHA_USERNAME', ''),
        'gastro_username': os.getenv('GASTRO_USERNAME', ''),
        'admin_chat_id': os.getenv('ADMIN_CHAT_ID', ''),  # Chat ID для личных уведомлений
        
        # Форум Shisha
        'forum_chat_id': os.getenv('FORUM_CHAT_ID', ''),
        'forum_thread_id': int(os.getenv('FORUM_THREAD_ID', '0')),
        
        # Форум Gastro
        'gastro_forum_chat_id': os.getenv('GASTRO_FORUM_CHAT_ID', ''),
        'gastro_forum_thread_id': int(os.getenv('GASTRO_FORUM_THREAD_ID', '0')),
        
        # Канал с описаниями вкусов
        'flavor_channel': os.getenv('FLAVOR_CHANNEL', ''),
        'flavor_thread_id': int(os.getenv('FLAVOR_THREAD_ID', '0')),
        
        # Файлы данных
        'final_assortment_file': 'data/FinalAssortment.json',
        'flavor_descriptions_file': 'data/FlavorDescriptions.json',
        'stock_data_file': 'data/StockData.json',
        'item_name_href_file': 'data/ItemNameHref.json',
        'agent_name_href_file': 'data/AgentNameHref.json',
        'menu_file': 'data/menu.json',
        
        # Бренды
        'actual_brands': [
            'Musthave', 'Darkside', 'Blackburn', 'DS shot', 'Chabacco', 'Nash',
            'Satyr', 'Xperience', 'Trofimoff\'s', 'Overdose', 'Starline', 'Энтузиаст'
        ],
        
        # Проекты (способы оплаты)
        'project_hrefs': {
            'наличные': os.getenv('CASH_PROJECT_HREF', ''),
            'иванкр': os.getenv('IVANQR_PROJECT_HREF', ''),
            'перевод': os.getenv('TRANSFER_PROJECT_HREF', '')
        },
        
        # Статусы заказов
        'order_states': {
            'botmanager': os.getenv('BOTMANAGER_STATE_HREF', ''),
            'доставлен': os.getenv('DELIVERED_STATE_HREF', '')
        }
    }
