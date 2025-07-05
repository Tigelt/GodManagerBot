
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import asyncio

BOT_TOKEN = "7261041875:AAFOSkUuITFSHqwy19fJgLBSakke-n5zEJs"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(">>> handle_message вызван")
    print(f"Текст: {update.message.text}")
    await update.message.reply_text("Принято твоё сообщение!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот активен, пиши любое сообщение.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()

