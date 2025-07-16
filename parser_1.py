async def parse_message(text, update):
    lines = [line.strip() for line in text.split('\n')]
    lines_iter = iter(lines)

    def next_non_empty():
        for line in lines_iter:
            if line.strip():
                return line.strip()
        return None

    # читаем строго по шаблону
    username = next_non_empty()
    payment = next_non_empty()
    summa = int(next_non_empty())
    delivery = int(next_non_empty())

    # комментарий до пустой строки
    comment = next_non_empty()

    # теперь адрес
    address = next_non_empty()
    # print(address)

    # товары
    total = 0
    items = []
    for line in lines_iter:
        if line.strip():
            parts = line.rsplit(' ', 2)
            if len(parts) < 3:
                await update.message.reply_text(f"Ошибка в строке товара: {line}")
                raise ValueError(f"Ошибка в строке товара: {line}")
            name = ' '.join(parts[:-2])
            quantity = int(parts[-2])
            price = int(parts[-1])
            items.append({
                'name': name,
                'quantity': quantity,
                'price': price
            })
            total += price

    if summa != total+delivery:
        await update.message.reply_text(f"Доставка в накладных расходах")

    await update.message.reply_text(
    f"Клиент: {username}\n"
    f"Оплата: {payment}\n"
    f"Сумма: {total}\n"
    f"Ручная сумма: {summa}\n"
    f"Доставка: {delivery}\n"
    f"Комментарий: {comment}\n"
    f"Адрес: {address}\n"
    f"Товары: {', '.join(['{} x{}'.format(i['name'], i['quantity']) for i in items])}"
)

    return {
        'Клиент': username,
        'Способ оплаты': payment,
        'Сумма': total,
        'Ручная сумма': summa,
        'Доставка': delivery,
        'Комментарий': comment,
        'Адрес': address,
        'Заказ': items
    }
