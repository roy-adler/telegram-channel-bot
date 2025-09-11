import os
import json
import sqlite3
import asyncio
import threading
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from api import run_api, set_bot_app

# Environment variables are loaded by docker-compose

# Debug: Print environment variables
print("Environment variables loaded:")
print(f"TELEGRAM_BOT_TOKEN: {os.environ.get('TELEGRAM_BOT_TOKEN', 'NOT SET')[:10]}...")
print(f"ADMIN_USER_ID: {os.environ.get('ADMIN_USER_ID', 'NOT SET')}")
print(f"API_KEY: {os.environ.get('API_KEY', 'NOT SET')}")

try:
    TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
    if not TOKEN or TOKEN == "your_bot_token_here":
        raise ValueError("TELEGRAM_BOT_TOKEN not set or using default value")
except KeyError:
    print("ERROR: TELEGRAM_BOT_TOKEN environment variable not found!")
    print("Please check your .env file or environment variables.")
    exit(1)
except ValueError as e:
    print(f"ERROR: {e}")
    print("Please set a valid TELEGRAM_BOT_TOKEN in your .env file.")
    exit(1)

ADMIN_USER_ID = os.environ.get("ADMIN_USER_ID", "")  # Your Telegram user ID

# Database setup
def init_database():
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect('data/bot_database.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            is_authenticated BOOLEAN DEFAULT FALSE,
            auth_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create groups table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY,
            group_title TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_database()

def get_user_auth_status(user_id):
    conn = sqlite3.connect('data/bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT is_authenticated FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else False

def authenticate_user(user_id, auth_code):
    conn = sqlite3.connect('data/bot_database.db')
    cursor = conn.cursor()
    
    # Check if auth code is valid (you can customize this logic)
    if auth_code == "admin123":  # Simple auth code for now
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, is_authenticated, auth_code, last_seen)
            VALUES (?, TRUE, ?, CURRENT_TIMESTAMP)
        ''', (user_id, auth_code))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def add_user_to_db(user_id, username, first_name, last_name):
    conn = sqlite3.connect('data/bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, last_seen)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()

def add_group_to_db(group_id, group_title):
    conn = sqlite3.connect('data/bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO groups (group_id, group_title, is_active)
        VALUES (?, ?, TRUE)
    ''', (group_id, group_title))
    conn.commit()
    conn.close()

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user_to_db(user.id, user.username, user.first_name, user.last_name)
    
    if get_user_auth_status(user.id):
        await update.message.reply_text(f"Hello {user.first_name}! You are authenticated. Welcome back!")
    else:
        keyboard = [[InlineKeyboardButton("Authenticate", callback_data="auth_request")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"Hello {user.first_name}! Please authenticate to use the bot's full features.",
            reply_markup=reply_markup
        )

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user_to_db(user.id, user.username, user.first_name, user.last_name)
    
    if get_user_auth_status(user.id):
        # Authenticated user gets personalized response
        await update.message.reply_text(f"Hey {user.first_name}! You're authenticated, so here's a special message for you! 🎉")
    else:
        # Non-authenticated user gets basic response
        await update.message.reply_text("Hey! Please authenticate first using /start command.")

async def handle_new_member(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle when new members are added to a group"""
    for member in update.message.new_chat_members:
        if member.id == ctx.bot.id:
            # Bot was added to a group
            group_title = update.effective_chat.title or "Unknown Group"
            add_group_to_db(update.effective_chat.id, group_title)
            await update.message.reply_text(
                f"Hello everyone! I'm your new bot assistant. "
                f"Please add me to your contacts and use /start to authenticate before using my features! 🤖"
            )
        else:
            # New human member added
            add_user_to_db(member.id, member.username, member.first_name, member.last_name)
            if get_user_auth_status(member.id):
                await update.message.reply_text(
                    f"Welcome {member.first_name}! I see you're already authenticated. "
                    f"Feel free to ask me anything! 😊"
                )
            else:
                await update.message.reply_text(
                    f"Welcome {member.first_name}! Please start a private chat with me and use /start to authenticate! 🔐"
                )

async def handle_callback_query(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "auth_request":
        await query.edit_message_text(
            "To authenticate, please send me a private message with:\n"
            "/auth <your_auth_code>\n\n"
            "Example: /auth admin123"
        )

async def auth_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle authentication command"""
    user = update.effective_user
    add_user_to_db(user.id, user.username, user.first_name, user.last_name)
    
    if len(ctx.args) == 0:
        await update.message.reply_text("Please provide an auth code. Usage: /auth <code>")
        return
    
    auth_code = ctx.args[0]
    if authenticate_user(user.id, auth_code):
        await update.message.reply_text("✅ Authentication successful! You now have access to all features!")
    else:
        await update.message.reply_text("❌ Invalid auth code. Please try again.")

async def status_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Check authentication status"""
    user = update.effective_user
    add_user_to_db(user.id, user.username, user.first_name, user.last_name)
    
    if get_user_auth_status(user.id):
        await update.message.reply_text("✅ You are authenticated!")
    else:
        await update.message.reply_text("❌ You are not authenticated. Use /auth <code> to authenticate.")

async def admin_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin command to view bot statistics"""
    user = update.effective_user
    if str(user.id) != ADMIN_USER_ID:
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    conn = sqlite3.connect('data/bot_database.db')
    cursor = conn.cursor()
    
    # Get user stats
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_authenticated = TRUE')
    auth_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM groups')
    total_groups = cursor.fetchone()[0]
    
    conn.close()
    
    stats_text = f"""
📊 Bot Statistics:
👥 Total Users: {total_users}
✅ Authenticated Users: {auth_users}
🏠 Active Groups: {total_groups}
    """
    
    await update.message.reply_text(stats_text)

app = (
    Application.builder()
    .token(TOKEN)
    .build()
)

# Add handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("auth", auth_command))
app.add_handler(CommandHandler("status", status_command))
app.add_handler(CommandHandler("stats", admin_stats))
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback_query))

if __name__ == "__main__":
    # Set the bot app for the API
    set_bot_app(app)
    
    # Start API server in a separate thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    print(f"API server started on port {os.environ.get('API_PORT', 5000)}")
    
    # Run the bot in polling mode
    print("Starting bot in polling mode...")
    app.run_polling()

