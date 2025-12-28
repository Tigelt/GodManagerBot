"""
Основной класс бота
Управляет всеми компонентами приложения
"""

import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import Update
from telegram.ext import ContextTypes

from services.moy_sklad import MoySkladAPI
from services.telegram_client import TelegramClientService
from services.google_sheets import GoogleSheetsService
from core.handlers.order_handler import OrderHandler
from core.handlers.assortment_handler import AssortmentHandler
from core.handlers.schedule_handler import ScheduleHandler

logger = logging.getLogger(__name__)

class GodManagerBot:
    """Основной класс бота"""
    
    def __init__(self, config):
        self.config = config
        
        # Инициализируем сервисы
        self.moy_sklad = MoySkladAPI(config['moy_sklad_token'], config)
        self.telegram_client = TelegramClientService(
            config['telegram_api_id'],
            config['telegram_api_hash'],
            config['session_file']
        )
        self.google_sheets = GoogleSheetsService(config['google_sheets_key_base64'])
        
        # Инициализируем обработчики
        self.assortment_handler = AssortmentHandler(self.telegram_client, self.moy_sklad, config)
        self.order_handler = OrderHandler(self.moy_sklad, self.google_sheets, self.telegram_client, config, self.assortment_handler)
        self.schedule_handler = None  # Будет инициализирован после создания app
        
        # Telegram Bot Application
        self.app = None
        
    def start(self):
        """Запуск бота"""
        try:
            # Инициализируем сервисы (синхронно)
            import asyncio
            asyncio.get_event_loop().run_until_complete(self.telegram_client.initialize())
            print("✅ Telegram клиент инициализирован")
            
            asyncio.get_event_loop().run_until_complete(self.google_sheets.initialize())
            print("✅ Google Sheets инициализирован")
            
            # Создаем Telegram Bot Application
            print(f"🔍 Bot token: {self.config['bot_token'][:10]}...")  # Показываем первые 10 символов
            self.app = ApplicationBuilder().token(self.config['bot_token']).build()
            
            # Регистрируем обработчики команд
            self._register_handlers()
            
            # Устанавливаем меню команд
            self._set_commands_menu()
            
          
            # Запускаем автопубликацию ассортимента
            #asyncio.get_event_loop().run_until_complete(self.assortment_handler.start_auto_publish())
            #print("✅ Автопубликация ассортимента запущена")
            
            # Запускаем бота
            print("🤖 Bot запущен")
            # Просто запускаем polling - это блокирующий вызов (как в старом проекте)
            self.app.run_polling()
            
        except Exception as e:
            print(f"❌ Ошибка запуска бота: {e}")
            raise
    
    def _register_handlers(self):
        """Регистрация обработчиков команд"""
        # Команды
        self.app.add_handler(CommandHandler("start", self._handle_start))
        self.app.add_handler(CommandHandler("assortment", self.assortment_handler.handle_assortment_command))
        self.app.add_handler(CommandHandler("updateassortment", self.assortment_handler.handle_update_assortment_command))
        self.app.add_handler(CommandHandler("baseflavor", self.assortment_handler.handle_base_flavor_command))
        self.app.add_handler(CommandHandler("inventory", self.assortment_handler.handle_inventory_command))
        self.app.add_handler(CommandHandler("publishmenu", self.assortment_handler.handle_publish_menu_command))
        
        # Обработчики сообщений
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # Обработчики кнопок
        self.app.add_handler(CallbackQueryHandler(self.order_handler.handle_callback))
        
        print("✅ Обработчики зарегистрированы")
    
    def _set_commands_menu(self):
        """Установка меню команд"""
        from telegram import BotCommand
        
        commands = [
            BotCommand("start", "Запуск бота"),
            BotCommand("assortment", "Публикация ассортимента"),
            BotCommand("updateassortment", "Обновление ассортимента"),
            BotCommand("baseflavor", "Обновление описаний вкусов"),
            BotCommand("inventory", "Показать инвентарь"),
            BotCommand("publishmenu", "Опубликовать меню (Gastro)")
        ]
        
        # Устанавливаем команды асинхронно
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            self.app.bot.set_my_commands(commands)
        )
        print("✅ Меню команд установлено")
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        chat_id = update.message.chat_id
        username = update.message.from_user.username
        await update.message.reply_text(f"🤖 GodManagerBot v2.0 запущен!\n\n🆔 Твой Chat ID: `{chat_id}`\n👤 Username: @{username}")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user = update.message.from_user.username
        
        # Определяем тип заказа по пользователю
        if user == self.config['shisha_username']:
            await self.order_handler.handle_shisha(update, context)
        elif user == self.config['gastro_username']:
            await self.order_handler.handle_gastro(update, context)
        else:
            await update.message.reply_text("❌ Неизвестный пользователь")
