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
import base64
import os


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
   
    if handler_name:
        # динамически вызовем нужную функцию
        await globals()[handler_name](update, context)
    else:
        await update.message.reply_text(f"Иди нахуй, {user}? Доступ закрыт.")
# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    #key_b64 = "ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAic2hpc2hhLTQ2NDgxMyIsCiAgInByaXZhdGVfa2V5X2lkIjogIjc4MWU5Mzk5NDRhZWYwNDMzMTNiYjFhNDIyNWIzMmI2MjU4YTliZWYiLAogICJwcml2YXRlX2tleSI6ICItLS0tLUJFR0lOIFBSSVZBVEUgS0VZLS0tLS1cbk1JSUV2UUlCQURBTkJna3Foa2lHOXcwQkFRRUZBQVNDQktjd2dnU2pBZ0VBQW9JQkFRQzJFcTZzZTd3U1U1T0Fcbjk1VEtiSW0zRVlJTGMyUWxjeDVQZ05FQW9TSnZwN0tZb0N4MWI5Wk45cXF1S3piQnBUUEpoeStTL2pFVGttRkNcbnZNWmY0SmFRSmNpTzNBNEg5TmhnT1FzRk52eStaekUxQ3JwdEZWNTFSRURsT1V0SGpGcU1UU0dMbCtZV3hFVXNcbnFTOEh1M1ljVzJrKzhZcVYvd2dZTjNkOWM2MC9EMlBGUzJUYjcwcVdZM1BNZlo5Tkd3bHI1ZmIzY3VrcGJuUEtcbnN5U1lZckRPendpd3FuZFVMa2JsWmJNNmJJS0h6SjVYNk1kSzRuN1pPOGNuenJYQ0p4Kzl1UE9IZ2J2U3A3VFJcbnNyUnVRRTloeEdtOW8xNkNRbW1idmxGVEZhOU5PeTgvZlMxbmhuTHAvL0p3WXRXZFpkUzRMdG1BS3BaVXk2ZW5cbjQ1MlNFZE05QWdNQkFBRUNnZ0VBRFQ2enJVRjlEM283OXp4TGV5UkZLbWVnSmJRWnUyMng3VWVxTEprTU44SWpcbnlGMlNqbUo1M1FjT0tJaGxQZFlHTytsVktTVExyaWhPWWZ2NGxGM3lwZjdScGE3VmFIZkR5OUFxZ0pFYzlyN3NcbkFmZExVNGNqN1hUdklaMjIzN2dTbURVK05QanlXSUtqbzVtVkhjTmgxck5CcHo0TC9saGtudHBlRzJhd1dpOWxcbkk0YVZYc05lMmNkY0p0UHphSkxsSjZuNkdZZ0dnSzRtVmpYRWhMSnhEVlU2dXhwekwzSmZjb1ByVDZyV1FadFhcbkNGREVWV3VCM3h0UTFVNWlpUzJzUlB1SWFWMDVYbmdjd21sWGxqQXJ5c044TGliZFBHTWxzcEVuUmQ0RFM0c05cbldlbUVDMTJjUmpXZG83bkVRR0FMRUdra2NxMyt6QzZMbG9UOHU1eGVBUUtCZ1FEN21jWXJRLzFZUUJYeDJUcmdcbjdRM1Z5bVhVYjdGRk1uUGEwVzJZU3NuWFlwTmFna2xvMHYrMzRjVlB0alpaMW5VQWRQUnArN1VjS1FoNGdtd1lcbkRWaXJiU0ZidW5pMXdlVkh1RTZXYUoyWDZpUHVJZ083Z3kzZVRLb1lBeDBHZEdBVys4Y3ROYUxyWXlVWW1wY0dcbkZJbDB5d05xTWlLNjRNT3lJcmM5SzBnd1BRS0JnUUM1UWE5dnM0OHFRU0tHNkRoeXNDYXJLREV2cjRNaXJheW5cbjFCUzVyY3dXOGRlL1BTbTAzUGsrU1hDTjJoQ2hBUEZYOEI3OTZCMVhZUU9uaU9NbDU3TXQyeXJxaHNyYlpKVFRcblFackg0L3NNbEpUY1NDWTc2V1NhQ1lYTkttdjk1bVZLR040eCtuQThFTUVqWWE1K1QzaEpkTzVqbE9NRnV1U0JcbkxyREFzNTlmQVFLQmdINkdKUmJLMlJOUkh2Z0JNcys3eGpKVjF3R09yWW5MeG1FcTRqOHNsUFlnVjFPem96RDRcbnNxb0krazJNcHlaa1ozQTBZRmtQd0ZNSiszMkdzTThqbnd5T0U3RnFRNXU3aHc2YkM4SXRsOXEyWHgwNHM4SFBcblJQaStldWNhWWJWR1ByQXdLMGg3NlpNUHg2N294cnZEQmlEYW1yd0R2RjFYL0hHUGJiQndISnhOQW9HQUhXbU5cblZmbTNJQ2xKTnd3RmNrZi9TNnRNNjlvOHdyTzZOc2NZSjBhdG9YTHlJdjJ0OG5ZbTZEbTJzZjdPSnhIRVA0YnpcbkZMTFdmYm44WDR2L0xGUjJBVERMeG9KeUVKVU9mOS9wbUJUZEZlazlIU0FqV2QyN1NDMTgzYzcvYUVjOUM1K1pcbkgydzRoNEROZVRXWUE1dlFhREUxYkFBR2J6RjErQUNXdFhHUE93RUNnWUVBblI0eHA0T3VNdFc4KzMzdktLV3ZcbktLUWJIZnRPYnNJUW1UaGoxNFg0Q2pzWm9vSWZqRGE1TXRVR0xXZ2U1UnN5dGdGN3k3Y21CVjlueGZ0SFM5U3NcbnJXTDRNcVJqUkY0aFVwb2VLQ1FkRFNSRUoyS1VZbERoVlBNMHhFYS92VFROdzJQdmtZTStodm1ZR0ZlUExMNU5cbm1XdWxVelpHK3NRRGFTK3pjN3dQY2RNPVxuLS0tLS1FTkQgUFJJVkFURSBLRVktLS0tLVxuIiwKICAiY2xpZW50X2VtYWlsIjogImdvZG1hbmFnZXJnb29nQHNoaXNoYS00NjQ4MTMuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLAogICJjbGllbnRfaWQiOiAiMTA5NjkzNTM3NjM2NDc1MTUwNDk0IiwKICAiYXV0aF91cmkiOiAiaHR0cHM6Ly9hY2NvdW50cy5nb29nbGUuY29tL28vb2F1dGgyL2F1dGgiLAogICJ0b2tlbl91cmkiOiAiaHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4iLAogICJhdXRoX3Byb3ZpZGVyX3g1MDlfY2VydF91cmwiOiAiaHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vb2F1dGgyL3YxL2NlcnRzIiwKICAiY2xpZW50X3g1MDlfY2VydF91cmwiOiAiaHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vcm9ib3QvdjEvbWV0YWRhdGEveDUwOS9nb2RtYW5hZ2VyZ29vZyU0MHNoaXNoYS00NjQ4MTMuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLAogICJ1bml2ZXJzZV9kb21haW4iOiAiZ29vZ2xlYXBpcy5jb20iCn0K"
    key_b64 = os.environ.get("KEY_JSON_BASE64")
    key_path = "shisha-464813-781e939944ae.json" 
    if key_b64:
        with open(key_path, "wb") as f:
            f.write(base64.b64decode(key_b64))
    else:
        raise RuntimeError("KEY_JSON_BASE64 is not set")
    
    print("Бот запущен...")
    app.run_polling()