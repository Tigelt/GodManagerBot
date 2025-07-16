from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from parser_1 import parse_message
from create_row_log import create_row_log
from create_row_shisha import create_row_shisha
from create_row_gastro import create_row_gastro
from create_order import *
from requestsMC.auto_ship_if_stocked import *
from requestsMC.reserve_order import *
from requestsMC.get_order_with_positions import *
from requestsMC.check_stock_for_order import *
from requestsMC.modifications import *
from configMC import BOT_TOKEN

from telegram import Update

# словарь: username -> обработчик
USER_HANDLERS = {
    "ShishaDanang": "handle_shisha",
    "Gastroheaven": "handle_gastro",
    "seanslov": "handle_elis"
}

# основные обработчики
async def handle_shisha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Это обработчик для ШИША. Делаю заказ в Мой Склад и пишу в Google Sheet...")
    data = await parse_message(update.message.text, update)
    response = create_row_shisha(data, update)
    response = create_row_log(data, update)
    response = create_order(data, update)

async def handle_gastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Это обработчик для ГАСТРО. Например, фиксирую заказ еды...")
    data = await parse_message(update.message.text, update)
    response = create_row_gastro(data, update)
    response = create_row_log(data, update)


async def handle_elis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("gfddsf")


# основной handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username
    handler_name = USER_HANDLERS.get(user)
    await update.message.reply_text("Принято")

    if handler_name:
        # динамически вызовем нужную функцию
        await globals()[handler_name](update, context)
    else:
        await update.message.reply_text(f"Иди нахуй, {user}? Доступ закрыт.")



# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    #app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    print("Бот запущен...")
    app.run_polling()