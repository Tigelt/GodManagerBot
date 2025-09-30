"""
Валидаторы для проверки данных
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def validate_order_data(order_data: Dict[str, Any]) -> bool:
    """
    Валидирует данные заказа
    
    Args:
        order_data: Словарь с данными заказа
        
    Returns:
        bool: True если данные валидны, False иначе
    """
    try:
        # Проверяем обязательные поля
        required_fields = ['username', 'payment_method', 'items']
        for field in required_fields:
            if field not in order_data:
                logger.error(f"Отсутствует обязательное поле: {field}")
                return False
                
        # Проверяем username
        if not order_data['username'] or not isinstance(order_data['username'], str):
            logger.error("Username должен быть непустой строкой")
            return False
            
        # Проверяем способ оплаты
        if not order_data['payment_method'] or not isinstance(order_data['payment_method'], str):
            logger.error("Способ оплаты должен быть непустой строкой")
            return False
            
        # Проверяем товары
        if not order_data['items'] or not isinstance(order_data['items'], list):
            logger.error("Список товаров должен быть непустым")
            return False
            
        # Проверяем каждый товар
        for item in order_data['items']:
            if not isinstance(item, dict):
                logger.error("Товар должен быть словарем")
                return False
                
            required_item_fields = ['name', 'quantity', 'price']
            for field in required_item_fields:
                if field not in item:
                    logger.error(f"В товаре отсутствует поле: {field}")
                    return False
                    
            # Проверяем типы и значения
            if not isinstance(item['name'], str) or not item['name']:
                logger.error("Название товара должно быть непустой строкой")
                return False
                
            if not isinstance(item['quantity'], int) or item['quantity'] <= 0:
                logger.error("Количество товара должно быть положительным числом")
                return False
                
            if not isinstance(item['price'], int) or item['price'] < 0:
                logger.error("Цена товара должна быть неотрицательным числом")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"Ошибка валидации данных заказа: {e}")
        return False
