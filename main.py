from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from parser_1 import parse_message
from create_row_log import create_row_log
from create_row_shisha import create_row_shisha
from create_row_gastro import create_row_gastro
from configMC import BOT_TOKEN
from create_order import create_order
from telegram import Update
from datetime import datetime
import pytz


# словарь: username -> обработчик
USER_HANDLERS = {
    "ShishaDanang": "handle_shisha",
    "Gastroheaven": "handle_gastro",
    "seanslov": "handle_elis"
}

# основные обработчики
async def handle_shisha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #await update.message.reply_text("Это обработчик для ШИША. Делаю заказ в Мой Склад и пишу в Google Sheet...")
    data = await parse_message(update.message.text, update)
    response = await create_order(data, update)
    response = await create_row_shisha(data, update)
    response = await create_row_log(data, update)

async def handle_gastro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #await update.message.reply_text("Это обработчик для ГАСТРО. Например, фиксирую заказ еды...")
    data = await parse_message(update.message.text, update)
    response = await create_row_gastro(data, update)
    response = await create_row_log(data, update)

async def handle_elis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("gfddsf")


# основной handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username
    handler_name = USER_HANDLERS.get(user)
    print("Время сервера UTC:", datetime.utcnow())
    print("Время сервера Asia/Ho_Chi_Minh:", datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")))

    if handler_name:
        # динамически вызовем нужную функцию
        await globals()[handler_name](update, context)
    else:
        await update.message.reply_text(f"Иди нахуй, {user}? Доступ закрыт.")
# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    print("Бот запущен...")
    app.run_polling()