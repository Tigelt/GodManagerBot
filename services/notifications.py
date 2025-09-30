"""
Сервис уведомлений
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class NotificationsService:
    """Сервис уведомлений"""
    
    def __init__(self):
        pass
    
    async def log_order_created(self, order_data: Dict[str, Any]):
        """Логирование создания заказа"""
        logger.info(f"Заказ создан: {order_data.get('username', 'N/A')}")
