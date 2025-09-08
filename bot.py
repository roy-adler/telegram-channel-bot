# pip install python-telegram-bot[webhooks]==21.4
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN        = os.environ["BOT_TOKEN"]                 # from @BotFather
TOKEN        = os.environ["BOT_API_URL"]               # Telegram bot api
PUBLIC_URL   = os.environ["PUBLIC_URL"].rstrip("/")    # e.g. https://my-bot.royadler.de
SECRET_TOKEN = os.environ.get("SECRET_TOKEN", "change-me")

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello from webhook!")

app = (
    Application.builder()
    .token(TOKEN)
    .base_url("https://telegram-bot-api.royadler.de/bot")
    .base_file_url("https://telegram-bot-api.royadler.de/file/bot")
    .build()
)
app.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=8080,
        webhook_path=f"/{TOKEN}",
        secret_token=SECRET_TOKEN,
        url=f"{PUBLIC_URL}/{TOKEN}",
        drop_pending_updates=True,
    )
