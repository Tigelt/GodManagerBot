"""
Сервис для работы с Google Sheets
"""

import base64
import logging
import os
import json
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """Сервис для работы с Google Sheets"""
    
    def __init__(self, key_base64: str):
        self.key_base64 = key_base64
        self.key_file_path = "google_sheets_key.json"
        self.gc = None  # gspread client
    
    async def initialize(self):
        """Инициализация сервиса"""
        try:
            # Создаем файл ключа из base64
            await self._create_key_file()
            
            # Инициализируем gspread (синхронная библиотека)
            import gspread
            from google.oauth2.service_account import Credentials
            
            # Настройка области доступа
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Загружаем учетные данные
            creds = Credentials.from_service_account_file(
                self.key_file_path, 
                scopes=scope
            )
            
            # Авторизуемся
            self.gc = gspread.authorize(creds)
            
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Google Sheets: {e}")
            raise
    
    async def _create_key_file(self):
        """Создание файла ключа из base64"""
        try:
            # Декодируем base64
            key_data = base64.b64decode(self.key_base64)
            
            # Сохраняем в файл
            with open(self.key_file_path, 'wb') as f:
                f.write(key_data)
            
            
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания файла ключа: {e}")
            raise
    
    async def write_to_sheet(self, spreadsheet_id: str, worksheet_name: str, data: List[List]) -> bool:
        """Запись данных в таблицу"""
        try:
            
            
            # Открываем таблицу
            spreadsheet = self.gc.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            # Записываем данные (как в старом проекте - вставляем в строку 4)
            
            worksheet.insert_row(data[0], index=4, value_input_option="USER_ENTERED")
            
            
            # Проверяем что данные действительно записались
            
            row_count = worksheet.row_count
            
            
            # Читаем последние строки для проверки
            if row_count > 0:
                last_rows = worksheet.get(f"A{row_count}:G{row_count}")
            
            
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи в таблицу: {e}")
            return False
    
    async def read_from_sheet(self, spreadsheet_id: str, worksheet_name: str, range_name: Optional[str] = None) -> List[List]:
        """Чтение данных из таблицы"""
        try:
            # Открываем таблицу
            spreadsheet = self.gc.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            # Читаем данные
            if range_name:
                data = worksheet.get(range_name)
            else:
                data = worksheet.get_all_values()
            
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Ошибка чтения из таблицы: {e}")
            return []
    
    async def update_cell(self, spreadsheet_id: str, worksheet_name: str, cell: str, value: str) -> bool:
        """Обновление ячейки"""
        try:
            # Открываем таблицу
            spreadsheet = self.gc.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            # Обновляем ячейку
            worksheet.update(cell, value)
            
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления ячейки: {e}")
            return False
    
    async def create_worksheet(self, spreadsheet_id: str, worksheet_name: str) -> bool:
        """Создание нового листа"""
        try:
            # Открываем таблицу
            spreadsheet = self.gc.open_by_key(spreadsheet_id)
            
            # Создаем лист
            spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
            
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания листа: {e}")
            return False
    
    async def get_worksheet_info(self, spreadsheet_id: str) -> List[Dict]:
        """Получение информации о листах"""
        try:
            # Открываем таблицу
            spreadsheet = self.gc.open_by_key(spreadsheet_id)
            
            # Получаем информацию о листах
            worksheets = []
            for worksheet in spreadsheet.worksheets():
                worksheets.append({
                    'title': worksheet.title,
                    'id': worksheet.id,
                    'row_count': worksheet.row_count,
                    'col_count': worksheet.col_count
                })
            
            
            return worksheets
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о листах: {e}")
            return []
    
    async def format_sheet(self, spreadsheet_id: str, worksheet_name: str, format_data: Dict) -> bool:
        """Форматирование листа"""
        try:
            # Открываем таблицу
            spreadsheet = self.gc.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            # Применяем форматирование
            if 'header_format' in format_data:
                worksheet.format('A1:Z1', format_data['header_format'])
            
            if 'data_format' in format_data:
                worksheet.format('A2:Z1000', format_data['data_format'])
            
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования листа: {e}")
            return False
