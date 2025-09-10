import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables from .env file
load_dotenv()

TOKEN        = os.environ["TELEGRAM_BOT_TOKEN"]                  # from @BotFather
BOT_API_URL  = os.environ["TELEGRAM_BOT_API_URL"].rstrip("/")
PUBLIC_URL   = os.environ["TELEGRAM_BOT_PUBLIC_URL"].rstrip("/")
SECRET_TOKEN = os.environ.get("TELEGRAM_BOT_SECRET_TOKEN", "change-me")

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello from webhook!")

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("hey")

app = (
    Application.builder()
    .token(TOKEN)
    .base_url(f"https://{BOT_API_URL}/bot")
    .base_file_url(f"https://{BOT_API_URL}/file/bot")
    .build()
)
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    # For testing, use polling instead of webhooks
    # Comment out the webhook line and uncomment the polling line below
    # app.run_webhook(
    #     listen="0.0.0.0",
    #     port=8080,
    #     secret_token=SECRET_TOKEN,
    #     webhook_url=f"{PUBLIC_URL}/{TOKEN}",
    #     drop_pending_updates=True,
    # )
    # Uncomment the line below for polling mode (easier for testing):
    app.run_polling()

