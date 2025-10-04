"""
Обработчик событий
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.moy_sklad import MoySkladAPI
from services.google_sheets import GoogleSheetsService
from utils.parsers import parse_order_message
from utils.validators import validate_order_data

logger = logging.getLogger(__name__)

class OrderHandler:
    """Обработчик событий"""
    
    def __init__(self, moy_sklad: MoySkladAPI, google_sheets: GoogleSheetsService, telegram_client, config: dict, assortment_handler=None):
        self.moy_sklad = moy_sklad
        self.google_sheets = google_sheets
        self.telegram_client = telegram_client
        self.config = config
        self.assortment_handler = assortment_handler
        self.notifications = None  # Будет инициализирован позже
    
    
    async def handle_shisha(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка заказов для ShishaDanang"""
        try:
            # Парсим сообщение
            order_data = await parse_order_message(update.message.text)
            
            # Валидируем данные
            if not validate_order_data(order_data):
                await update.message.reply_text("❌ Ошибка в данных заказа")
                return
            
            # Создаем заказ в Мой Склад
            order = await self.moy_sklad.create_order(order_data)
            order_href = order.get("meta", {}).get("href")
            
            if not order_href:
                await update.message.reply_text("❌ Ошибка создания заказа")
                return
            
            # Меняем статус заказа на Bot Manager
            botmanager_state_href = self.config.get('order_states', {}).get('botmanager')
            if botmanager_state_href:
                await self.moy_sklad.change_order_state(order_href, botmanager_state_href)
                print("🔄 Статус заказа изменен на Bot Manager")
            
            # Сохраняем заказ в контексте (как в старом проекте)
            context.user_data["last_order"] = order
            context.user_data["last_order_data"] = order_data
            
            # Отправляем сообщение о создании заказа
            await update.message.reply_text("✅ Заказ создан в МС")
             
            # Записываем заказ в Google Sheets
            await self._write_order_to_sheets(order_data, update)
            print("✅ Заказ записан в Google Sheets")
            await update.message.reply_text("📊 Заказ записан в Google Sheets")
            
            # Создаем кнопки подтверждения
            message = await self.get_order_message(order_href, order_data.get('overheads'))
            keyboard = [
                [
                    InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_order"),
                    InlineKeyboardButton("❌ Отменить", callback_data="cancel_order")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Отправляем сообщение с кнопками
            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
            )
            
            # Сохраняем заказ в контексте
            context.user_data["last_order"] = order
            
        except Exception as e:
            
            await update.message.reply_text("❌ Ошибка создания заказа")
    
    async def handle_gastro(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка заказов для Gastroheaven"""
        try:
            # Парсим сообщение
            order_data = await parse_order_message(update.message.text)
            
            # Валидируем данные
            if not validate_order_data(order_data):
                await update.message.reply_text("❌ Ошибка в данных заказа")
                return
            
            # Для Gastro только записываем в Google Sheets
            await self._write_order_to_sheets(order_data, update)
            
            # Отправляем подтверждение
            await update.message.reply_text(
                f"✅ Заказ от {order_data.get('username', 'N/A')} записан в Gastro таблицы"
            )
            
            # Логируем
            if self.notifications:
                self.notifications.log_order_created(order_data)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки заказа Gastro: {e}")
            await update.message.reply_text("❌ Ошибка записи заказа")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback кнопок"""
        query = update.callback_query
        await query.answer()
        
        try:
            data = query.data.split(":")
            action = data[0]
            
            if action == "confirm_order":
                order_href = data[1] if len(data) > 1 else None
                order_data = context.user_data.get("last_order_data", {})
                overheads = order_data.get("overheads", 0)
                await self._confirm_order(query, context, order_href, overheads, update)
            elif action == "cancel_order":
                await self._cancel_order(query, context)
            else:
                await query.edit_message_text("❌ Неизвестная команда")
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки callback: {e}")
            await query.edit_message_text("❌ Ошибка обработки")
    
    async def _confirm_order(self, query, context: ContextTypes.DEFAULT_TYPE, order_href: str, overheads: int, update):
        """Подтверждение заказа"""
        try:
            # Получаем заказ из контекста
            order = context.user_data.get("last_order")
            if not order:
                await query.edit_message_text("❌ Заказ не найден в контексте")
                return
            
            # Получаем позиции заказа для отображения
            order_href = order.get("meta", {}).get("href")
            order_message = await self.get_order_message(order_href, overheads)
            print("✅ Заказ подтверждён.")
            # Обновляем сообщение с подтверждением и товарами
            await query.edit_message_text(
                f"✅ ПОДТВЕРЖДЕНО\n\n{order_message}",
            )
            
            # Создаем платеж
            payment = await self.moy_sklad.create_payment(order_href)
            
            print("💰 Платёж создан")
            await query.message.reply_text("💰 Платёж создан.")
            
            # Создаем отгрузку
            order_data = context.user_data.get("last_order_data")
            overheads = order_data.get("overheads", False)
            demand = await self.moy_sklad.create_demand(order_href, overheads)
            # Отправляем отдельное сообщение об отгрузке
            await query.message.reply_text("📦 Отгрузка создана.")
            print("📦 Отгрузка создана")
            # Обновляем ассортимент после отгрузки
            if self.assortment_handler:
                # Сначала обновляем данные из Мой Склад
                await self.assortment_handler._prepare_assortment()
                # Потом обновляем сообщения в форуме
                await self.assortment_handler._update_assortment(update, context)
                await query.message.reply_text("🔄 Ассортимент обновлен после отгрузки")
            
            # Меняем статус заказа на "доставлен"
            delivered_state_href = self.config.get('order_states', {}).get('доставлен')
            if delivered_state_href:
                await self.moy_sklad.change_order_state(order_href, delivered_state_href)
                print("🔄 Статус заказа изменен на Доставлен")
                
        
            
                 
        except Exception as e:
            logger.error(f"❌ Ошибка подтверждения заказа: {e}")
            await query.edit_message_text("❌ Ошибка подтверждения заказа")
    
    
    async def _cancel_order(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Отмена заказа"""
        try:
            
            order = context.user_data.get("last_order")
            if not order:
                await query.edit_message_text("❌ Заказ не найден в контексте")
                return
            
            # Получаем позиции заказа для отображения
            order_href = order.get("meta", {}).get("href")
            order_data = context.user_data.get("last_order_data")
            overheads = order_data.get("overheads", False)
            cancel_message = await self.get_order_message(order_href, overheads)
            
            await query.edit_message_text(
                f"❌ **Отменено**\n\n{cancel_message}",
            )
                      
        except Exception as e:
            logger.error(f"❌ Ошибка отмены заказа: {e}")
            await query.edit_message_text("❌ Ошибка отмены заказа")
    
    
    async def get_order_message(self, order_href: str, overheads: int) -> str:
        """Возвращает готовое сообщение с деталями заказа по order_href"""
        # Получаем заказ из Мой Склад
        order = await self.moy_sklad.get_order_by_href(order_href)
        if not order:
            return "❌ Заказ не найден"
        
        # Получаем позиции заказа
        positions = await self.moy_sklad.get_order_positions(order_href)
        
        # Получаем агента для имени клиента
        agent_href = order.get('agent', {}).get('meta', {}).get('href')
        client_name = 'Не указано'
        if agent_href:
            client_name = await self.moy_sklad.get_agent_by_href(agent_href)
    
        
        # Считаем накладные расходы из заказа
        order_sum = order.get('sum', 0) / 100000
        delivery_cost = int(order.get('description', 0))
        # Если есть доставка - это накладные расходы
    
        
        # Формируем сообщение
        message = f"Клиент: {client_name}\n"
        message += f"Сумма: {order.get('sum', 0) / 100000}\n"
        message += f"Доставка: {order.get('description', 'N/A')}\n"
        message += f"Накладные расходы: {overheads}\n\n"
        
        # Добавляем товары из Мой Склад
        message += "Заказ:\n"
        for product_name, product_data in positions.items():
            quantity = product_data.get('quantity', 0)
            price = product_data.get('price', 0)
            message += f"• {product_name} x{quantity:.0f} — {price:.0f}\n"
        
        return message
    
    async def _write_order_to_sheets(self, order_data: dict, update):
        """Универсальная запись заказа в Google Sheets (Shisha/Gastro)"""
        try:
            

            spreadsheet_id = self.config['spreadsheet_id']  # Одна таблица
            # Определяем тип заказа (Shisha/Gastro) по ОТПРАВИТЕЛЮ
            sender_username = update.message.from_user.username
             
            if sender_username == self.config['shisha_username']:
                sheet_type = "Shisha"
                worksheet_name = self.config['shisha_worksheet_name']  # Из конфига
                
            elif sender_username == self.config['gastro_username']:
                sheet_type = "Gastro"
                worksheet_name = self.config['gastro_worksheet_name']  # Из конфига
                
            else:
                sheet_type = "Unknown"
                print(f"⚠️ НЕИЗВЕСТНЫЙ ОТПРАВИТЕЛЬ: {sender_username}")
                worksheet_name = self.config['gastro_worksheet_name']  # Из конфига
            
            # Формируем данные для записи (как в старом проекте)
            from datetime import timedelta
            now = datetime.utcnow() + timedelta(hours=7)
            date = now.strftime("%d.%m")
     
            username = order_data.get('username', '').lstrip('@')  # удаляет @ в начале
            
            # Получаем полное имя через Telethon (как в старом проекте)
            full_name = await self.telegram_client.get_full_name(f"@{username}")
            client_link = f'=HYPERLINK("https://t.me/{username}"; "{full_name} @{username}")'
            
            comment = order_data.get('comment', '')
            delivery = order_data.get('delivery_cost', '')
            
            # Способ оплаты (как в старом проекте)
            cash = ''
            ivanqr = ''
            transfer = ''
            
            payment = order_data.get('payment_method', '').lower()
            summa = order_data.get('total', 0)
            
            
            
            if 'наличные' in payment:
                cash = summa
            elif 'иванкр' in payment:
                ivanqr = summa
            elif 'перевод' in payment:
                transfer = summa
            else:
                cash = summa
            
            
            # Собираем строку для таблицы (как в старом проекте)
            row_data = [date, client_link, comment, delivery, cash, ivanqr, transfer]
                   
            # Записываем в таблицу
            result = await self.google_sheets.write_to_sheet(
                spreadsheet_id=spreadsheet_id,
                worksheet_name=worksheet_name,
                data=[row_data]
            )
            
            print(f"✅ Заказ {sheet_type} записан в Google Sheets")
            
        except Exception as e:
            print(f"❌ Ошибка записи заказа в Google Sheets: {e}")
            # Не поднимаем исключение, чтобы не сломать основной поток
    
