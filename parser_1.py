from telethon import TelegramClient
from configMC import headers, ABBREVIATIONS

async def parse_message(text, update):
    lines = [line.strip() for line in text.split('\n')]
    lines_iter = iter(lines)
    
    # Функция для получения следующей непустой строки
    def next_non_empty():
        for line in lines_iter:
            if line.strip():
                return line.strip()
        return None
    # читаем строго по шаблону
    username = next_non_empty()
    usernameME = await get_full_name(username)
    user = f"{usernameME} {username}"
    #print(f"Получено сообщение от {username} ({usernameME})")

    payment = next_non_empty()
    summa = int(next_non_empty())
    delivery = int(next_non_empty())
    comment = next_non_empty()
    #address = next_non_empty()
    #number = next_non_empty()
    #number = number[1:] if number.startswith('+') else number
    address = ''
    number = ''

    # товары
    total = 0
    items = []
    for line in lines_iter:
        if line.strip():
            parts = line.rsplit(' ', 2)
            if len(parts) < 3:
                await update.message.reply_text(f"Ошибка в строке товара: {line}")
                raise ValueError(f"Ошибка в строке товара: {line}")
            name = ' '.join(parts[:-2]).lower()
            quantity = int(parts[-2])
            price = int(parts[-1])
            
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


    await update.message.reply_text(
    f"Клиент: {user}\n"
    f"Оплата: {payment}\n"
    #f"Сумма: {total}\n"
    f"Ручная сумма: {summa}\n"
    f"Сумма заказа: {total}\n"
    f"Доставка: {delivery}\n"
    #f"Комментарий: {comment}\n"
    #f"Адрес: {address}\n"
    #f"Номер: {number}\n"
    #f"Товары: {', '.join(['{} x{}'.format(i['name'], i['quantity']) for i in items])}"
)

    return {
        'username': username,
        'full_name': user,
        'payment': payment,
        'total': total,
        'summa': summa,
        'delivery': delivery,
        'comment': comment,
        'address': address,
        'number': number,
        'items': items
    }



async def get_full_name(username):
    API_ID = 20732915
    API_HASH = '76a13ac0c9479ad595d3a0f71be8e43d'   

    try:
        async with TelegramClient('aimanager', API_ID, API_HASH) as client:
            user = await client.get_entity(username)
            full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            return full_name
    except Exception as e:
        print(f"⚠️ Не удалось получить имя для {username}: {e}")
        return ""