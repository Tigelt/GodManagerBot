"""
Парсеры для обработки сообщений
"""
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Сокращения брендов
ABBREVIATIONS = {
    "bb": "Blackburn",
    "cb": "Chabacco", 
    "ds": "Darkside",
    "mh": "Musthave",
    "sl": "Starline",
    "od": "Overdose",
    "энт": "Энтузиаст",
    "sr": "Satyr"
}

async def parse_order_message(text: str) -> Dict[str, Any]:
    """
    Парсит сообщение с заказом и возвращает структурированные данные
    
    Формат сообщения:
    username
    payment_method
    manual_sum
    delivery_cost
    comment
    item_name quantity price
    item_name quantity price
    ...
    """
    try:
        lines = [line.strip() for line in text.split('\n')]
        lines_iter = iter(lines)
        
        # Функция для получения следующей непустой строки
        def next_non_empty():
            for line in lines_iter:
                if line.strip():
                    return line.strip()
            return None
            
        # Читаем данные по шаблону
        username = next_non_empty()
        if not username:
            raise ValueError("Не указан username")
            
        payment_method = next_non_empty()
        if not payment_method:
            raise ValueError("Не указан способ оплаты")
            
        manual_sum = int(next_non_empty())
        delivery_cost = int(next_non_empty())
        comment = next_non_empty() or ""
        
        # Парсим товары
        total = 0
        items = []
        
        for line in lines_iter:
            if line.strip():
                parts = line.rsplit(' ', 2)
                if len(parts) < 3:
                    raise ValueError(f"Ошибка в строке товара: {line}")
                    
                name = ' '.join(parts[:-2]).lower()
                quantity = int(parts[-2])
                price = int(parts[-1])
                
                # Заменяем сокращения на полные названия
                for abbr, full in ABBREVIATIONS.items():
                    if name.startswith(abbr + " "):
                        name = name.replace(abbr, full, 1)
                        break
                        
                items.append({
                    'name': name,
                    'quantity': quantity,
                    'price': price
                })
                total += price
        
        # Определяем накладные расходы (как в старом проекте)
        overheads = 0
        # Накладные = доставка, только если сумма товаров + доставка = указанная сумма
        if manual_sum - delivery_cost < total:
            overheads = delivery_cost
        
        result = {
            'username': username,
            'payment_method': payment_method,
            'manual_sum': manual_sum,
            'delivery_cost': delivery_cost,
            'comment': comment,
            'total': total,
            'overheads': overheads,
            'items': items
        }
        
        print("🔍 DEBUG PARSER - ВСЕ ДАННЫЕ:")
        print(f"  username: {username}")
        print(f"  payment_method: {payment_method}")
        print(f"  manual_sum: {manual_sum}")
        print(f"  delivery_cost: {delivery_cost}")
        print(f"  comment: {comment}")
        print(f"  total: {total}")
        print(f"  overheads: {overheads}")
        print(f"  items: {items}")
        print(f"  РАСЧЕТ: total({total}) != manual_sum({manual_sum}) = {total != manual_sum}")
        print(f"  РЕЗУЛЬТАТ: overheads = {overheads}")
        print("=" * 60)
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка парсинга сообщения: {e}")
        raise ValueError(f"Ошибка парсинга заказа: {e}")
