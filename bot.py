import os
import json
import sqlite3
import asyncio
import threading
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from api import run_api, set_bot_app
from db import (
    init_database, create_default_channel, add_user_to_db, get_user_auth_status,
    get_user_channel_info, authenticate_user, authenticate_user_legacy, deauthenticate_user, add_group_to_db,
    add_user_to_group, remove_user_from_group, create_channel, get_channel_by_secret,
    get_all_channels, get_users_in_channel, get_bot_stats, get_debug_info
)

# Environment variables are loaded by docker-compose

# Debug: Print environment variables
print("Environment variables loaded:")
print(f"TELEGRAM_BOT_TOKEN: {os.environ.get('TELEGRAM_BOT_TOKEN', 'NOT SET')[:10]}...")
print(f"ADMIN_USER_ID: {os.environ.get('ADMIN_USER_ID', 'NOT SET')}")
print(f"TELEGRAM_BOT_API_KEY: {os.environ.get('TELEGRAM_BOT_API_KEY', 'NOT SET')}")

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

# Database initialization is now handled by db.py

# Initialize database
init_database()
create_default_channel()

# All database functions are now imported from db.py

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not user:
            await update.message.reply_text("❌ Unable to identify user.")
            return
            
        add_user_to_db(user.id, user.username, user.first_name, user.last_name)
        
        is_authenticated, channel_id = get_user_auth_status(user.id)
        if is_authenticated:
            channel_info = get_user_channel_info(user.id)
            if channel_info and channel_info[2]:  # channel_name
                await update.message.reply_text(
                    f"Hello {user.first_name}! You are authenticated to channel '{channel_info[2]}'. Welcome back!"
                )
            else:
                await update.message.reply_text(f"Hello {user.first_name}! You are authenticated. Welcome back!")
        else:
            keyboard = [[InlineKeyboardButton("Join Channel", callback_data="auth_request")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"Hello {user.first_name}! Please join a channel to use the bot's full features.",
                reply_markup=reply_markup
            )
    except Exception as e:
        print(f"Error in start command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages - just log, don't respond"""
    try:
        user = update.effective_user
        if not user:
            return  # Skip if no user info
        
        # Just log the message, don't do any database operations
        print(f"Message from {user.first_name} (@{user.username}): {update.message.text[:50]}...")
        
        # Don't respond to regular messages - only respond to commands
        # This prevents the bot from replying to every message in groups
    except Exception as e:
        print(f"Error in handle_message: {e}")
        # Don't re-raise the exception to prevent bot crashes

async def handle_new_member(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle when new members are added to a group"""
    try:
        for member in update.message.new_chat_members:
            if member.id == ctx.bot.id:
                # Bot was added to a group
                group_title = update.effective_chat.title or "Unknown Group"
                add_group_to_db(update.effective_chat.id, group_title)
                await update.message.reply_text(
                    f"Hello everyone! I'm your new bot assistant. "
                    f"Please add me to your contacts and use /start to join a channel before using my features! 🤖"
                )
            else:
                # New human member added
                add_user_to_db(member.id, member.username, member.first_name, member.last_name)
                # Add user to the group
                add_user_to_group(update.effective_chat.id, member.id)
                
                is_authenticated, channel_id = get_user_auth_status(member.id)
                if is_authenticated:
                    channel_info = get_user_channel_info(member.id)
                    if channel_info and channel_info[2]:  # channel_name
                        await update.message.reply_text(
                            f"Welcome {member.first_name}! I see you're already in channel '{channel_info[2]}'. "
                            f"Feel free to ask me anything! 😊"
                        )
                    else:
                        await update.message.reply_text(
                            f"Welcome {member.first_name}! I see you're already authenticated. "
                            f"Feel free to ask me anything! 😊"
                        )
                else:
                    await update.message.reply_text(
                        f"Welcome {member.first_name}! Please start a private chat with me and use /start to join a channel!\n"
                        f"Use: /join <channel_name> <channel_secret> 🔐"
                    )
    except Exception as e:
        print(f"Error in handle_new_member: {e}")
        # Don't re-raise the exception to prevent bot crashes

async def handle_callback_query(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "auth_request":
        await query.edit_message_text(
            "To join a channel, please send me a private message with:\n"
            "/join <channel_name> <channel_secret>\n\n"
            "Example: /join general welcome123\n\n"
            "Ask your administrator for the channel name and secret to join."
        )

async def join_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle channel join command"""
    try:
        user = update.effective_user
        if not user:
            await update.message.reply_text("❌ Unable to identify user.")
            return
            
        add_user_to_db(user.id, user.username, user.first_name, user.last_name)
        
        # Always ensure the user is tracked in the current chat (group or private)
        if update.effective_chat.type in ['group', 'supergroup']:
            add_group_to_db(update.effective_chat.id, update.effective_chat.title or "Unknown Group")
            add_user_to_group(update.effective_chat.id, user.id)
            print(f"User {user.id} joined group {update.effective_chat.id}")
        
        if len(ctx.args) == 0:
            await update.message.reply_text(
                "Please provide both channel name and secret.\n"
                "Usage: /join <channel_name> <channel_secret>\n"
                "Example: /join general welcome123"
            )
            return
        elif len(ctx.args) == 1:
            # Legacy support: try with just secret first, then show new format message
            channel_secret = ctx.args[0]
            success, channel_name_verified, description = authenticate_user_legacy(user.id, channel_secret)
            if success:
                await update.message.reply_text(
                    f"✅ Successfully joined channel '{channel_name_verified}'!\n"
                    f"ℹ️ Note: In the future, please use: /join {channel_name_verified} {channel_secret}\n"
                    + (f"\nChannel description: {description}" if description else "")
                    + ("\n\nYou can now receive broadcasts in this group!" if update.effective_chat.type in ['group', 'supergroup'] else "")
                )
                return
            else:
                await update.message.reply_text(
                    "❌ Invalid channel secret.\n"
                    "Please use the new format: /join <channel_name> <channel_secret>\n"
                    "Example: /join general welcome123\n"
                    "Ask your administrator for both the channel name and secret."
                )
                return
        else:
            # New format with both channel name and secret
            channel_name = ctx.args[0]
            channel_secret = ctx.args[1]
            success, channel_name_verified, description = authenticate_user(user.id, channel_name, channel_secret)
        
        if success:
            message = f"✅ Successfully joined channel '{channel_name_verified}'!"
            if description:
                message += f"\n\nChannel description: {description}"
            
            # Add helpful message for group users
            if update.effective_chat.type in ['group', 'supergroup']:
                message += f"\n\nYou can now receive broadcasts in this group!"
            
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("❌ Invalid channel name or secret. Please check with your administrator.")
    except Exception as e:
        print(f"Error in join_command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

async def leave_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle channel leave command"""
    try:
        user = update.effective_user
        if not user:
            await update.message.reply_text("❌ Unable to identify user.")
            return
            
        add_user_to_db(user.id, user.username, user.first_name, user.last_name)
        
        is_authenticated, channel_id = get_user_auth_status(user.id)
        if not is_authenticated:
            await update.message.reply_text("❌ You are not currently in any channel.")
            return
        
        # Remove user from channel
        deauthenticate_user(user.id)
        
        await update.message.reply_text("✅ You have left the channel. Use /join <channel_secret> to join another channel.")
    except Exception as e:
        print(f"Error in leave_command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

async def stop_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle stop command - remove user from group and deauthenticate"""
    try:
        user = update.effective_user
        if not user:
            await update.message.reply_text("❌ Unable to identify user.")
            return
            
        add_user_to_db(user.id, user.username, user.first_name, user.last_name)
        
        # Check if user is in a group
        if update.effective_chat.type in ['group', 'supergroup']:
            # Remove user from the group
            remove_user_from_group(update.effective_chat.id, user.id)
            print(f"User {user.id} removed from group {update.effective_chat.id}")
            
            # Also deauthenticate the user
            deauthenticate_user(user.id)
            
            await update.message.reply_text(
                f"✅ {user.first_name}, you have been removed from this group and deauthenticated.\n"
                f"You will no longer receive broadcasts here.\n"
                f"Use /join <channel_secret> to rejoin if needed."
            )
        else:
            # If not in a group, just deauthenticate
            deauthenticate_user(user.id)
            
            await update.message.reply_text(
                f"✅ {user.first_name}, you have been deauthenticated.\n"
                f"You will no longer receive broadcasts.\n"
                f"Use /join <channel_secret> to rejoin if needed."
            )
            
    except Exception as e:
        print(f"Error in stop_command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

async def status_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Check authentication status"""
    try:
        user = update.effective_user
        if not user:
            await update.message.reply_text("❌ Unable to identify user.")
            return
            
        add_user_to_db(user.id, user.username, user.first_name, user.last_name)
        
        # If this is a group message, ensure the user is tracked in the group
        if update.effective_chat.type in ['group', 'supergroup']:
            add_group_to_db(update.effective_chat.id, update.effective_chat.title or "Unknown Group")
            add_user_to_group(update.effective_chat.id, user.id)
        
        is_authenticated, channel_id = get_user_auth_status(user.id)
        if is_authenticated:
            channel_info = get_user_channel_info(user.id)
            if channel_info and channel_info[2]:  # channel_name
                await update.message.reply_text(f"✅ You are in channel '{channel_info[2]}'")
            else:
                await update.message.reply_text("✅ You are authenticated!")
        else:
            await update.message.reply_text("❌ You are not in any channel. Use /join <channel_secret> to join a channel.")
    except Exception as e:
        print(f"Error in status_command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

async def register_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Register user in current group for broadcasts"""
    try:
        user = update.effective_user
        if not user:
            await update.message.reply_text("❌ Unable to identify user.")
            return
            
        add_user_to_db(user.id, user.username, user.first_name, user.last_name)
        
        if update.effective_chat.type in ['group', 'supergroup']:
            add_group_to_db(update.effective_chat.id, update.effective_chat.title or "Unknown Group")
            add_user_to_group(update.effective_chat.id, user.id)
            await update.message.reply_text(
                f"✅ {user.first_name}, you are now registered in this group!\n"
                f"Use /join <channel_secret> to authenticate and receive broadcasts."
            )
        else:
            await update.message.reply_text("❌ This command only works in groups.")
    except Exception as e:
        print(f"Error in register_command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

async def admin_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin command to view bot statistics"""
    user = update.effective_user
    if str(user.id) != ADMIN_USER_ID:
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    stats = get_bot_stats()
    total_users = stats['total_users']
    auth_users = stats['authenticated_users']
    total_groups = stats['total_groups']
    total_channels = stats['total_channels']
    channel_stats = stats['channel_distribution']
    
    stats_text = f"""
📊 Bot Statistics:
👥 Total Users: {total_users}
✅ Authenticated Users: {auth_users}
🏠 Active Groups: {total_groups}
📺 Total Channels: {total_channels}

📺 Channel Distribution:
"""
    
    for channel_name, user_count in channel_stats:
        stats_text += f"• {channel_name}: {user_count} users\n"
    
    await update.message.reply_text(stats_text)

async def admin_create_channel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin command to create a new channel"""
    user = update.effective_user
    if str(user.id) != ADMIN_USER_ID:
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    if len(ctx.args) < 2:
        await update.message.reply_text(
            "Usage: /create_channel <channel_name> <channel_secret> [description]\n"
            "Example: /create_channel announcements secret123 This is for announcements"
        )
        return
    
    channel_name = ctx.args[0]
    channel_secret = ctx.args[1]
    description = " ".join(ctx.args[2:]) if len(ctx.args) > 2 else ""
    
    success, message = create_channel(channel_name, channel_secret, description, user.id)
    
    if success:
        response = f"✅ Channel '{channel_name}' created successfully!\n"
        response += f"Secret: `{channel_secret}`\n"
        if description:
            response += f"Description: {description}"
        await update.message.reply_text(response, parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ {message}")

async def admin_list_channels(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin command to list all channels"""
    user = update.effective_user
    if str(user.id) != ADMIN_USER_ID:
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    channels = get_all_channels()
    
    if not channels:
        await update.message.reply_text("📺 No channels found.")
        return
    
    response = "📺 Available Channels:\n\n"
    for channel_id, channel_name, description, is_active, created_at, user_count in channels:
        status = "🟢 Active" if is_active else "🔴 Inactive"
        response += f"**{channel_name}** {status}\n"
        response += f"ID: {channel_id} | Users: {user_count}\n"
        if description:
            response += f"Description: {description}\n"
        response += f"Created: {created_at}\n\n"
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def admin_channel_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin command to list users in a specific channel"""
    user = update.effective_user
    if str(user.id) != ADMIN_USER_ID:
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    if len(ctx.args) == 0:
        await update.message.reply_text("Usage: /channel_users <channel_id>")
        return
    
    try:
        channel_id = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("❌ Channel ID must be a number.")
        return
    
    # Get channel info from all channels
    all_channels = get_all_channels()
    channel = None
    for ch in all_channels:
        if ch[0] == channel_id:  # channel_id is first element
            channel = (ch[1],)  # channel_name is second element
            break
    
    if not channel:
        await update.message.reply_text(f"❌ Channel with ID {channel_id} not found.")
        return
    
    users = get_users_in_channel(channel_id)
    channel_name = channel[0]
    
    if not users:
        await update.message.reply_text(f"📺 No users found in channel '{channel_name}'.")
        return
    
    response = f"👥 Users in channel '{channel_name}':\n\n"
    for user_id, username, first_name, last_name, last_seen in users:
        display_name = f"{first_name} {last_name}".strip() or username or f"User {user_id}"
        response += f"• {display_name} (@{username or 'N/A'})\n"
        response += f"  ID: {user_id} | Last seen: {last_seen}\n\n"
    
    await update.message.reply_text(response)

async def admin_debug_groups(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin command to debug group and user tracking"""
    user = update.effective_user
    if str(user.id) != ADMIN_USER_ID:
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    debug_info = get_debug_info()
    groups = debug_info['groups']
    group_members = debug_info['group_members']
    auth_users = debug_info['authenticated_users']
    
    response = "🔍 **Debug Information**\n\n"
    
    # Groups section
    response += f"📊 **Groups ({len(groups)}):**\n"
    for group_id, group_title, is_active in groups:
        status = "🟢" if is_active else "🔴"
        response += f"{status} {group_title} (ID: {group_id})\n"
    
    # Group members section
    response += f"\n👥 **Group Members ({len(group_members)}):**\n"
    current_group = None
    for group_id, group_title, user_id, username, first_name, is_authenticated in group_members:
        if current_group != group_id:
            response += f"\n**{group_title} (ID: {group_id}):**\n"
            current_group = group_id
        
        auth_status = "✅" if is_authenticated else "❌"
        display_name = first_name or username or f"User {user_id}"
        response += f"  {auth_status} {display_name} (@{username or 'N/A'})\n"
    
    # Authenticated users section
    response += f"\n🔐 **Authenticated Users ({len(auth_users)}):**\n"
    for user_id, username, first_name, last_name, is_authenticated, channel_id in auth_users:
        display_name = f"{first_name} {last_name}".strip() or username or f"User {user_id}"
        response += f"• {display_name} (@{username or 'N/A'}) - Channel: {channel_id}\n"
    
    await update.message.reply_text(response, parse_mode='Markdown')

app = (
    Application.builder()
    .token(TOKEN)
    .build()
)

# Add handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("join", join_command))
app.add_handler(CommandHandler("leave", leave_command))
app.add_handler(CommandHandler("stop", stop_command))
app.add_handler(CommandHandler("status", status_command))
app.add_handler(CommandHandler("register", register_command))
app.add_handler(CommandHandler("stats", admin_stats))
app.add_handler(CommandHandler("create_channel", admin_create_channel))
app.add_handler(CommandHandler("list_channels", admin_list_channels))
app.add_handler(CommandHandler("channel_users", admin_channel_users))
app.add_handler(CommandHandler("debug_groups", admin_debug_groups))
async def handle_left_member(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle when members leave a group"""
    if update.message.left_chat_member:
        member = update.message.left_chat_member
        if member.id != ctx.bot.id:  # Don't remove the bot from group_members
            remove_user_from_group(update.effective_chat.id, member.id)

app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_left_member))
# Minimal message handler - just logs, doesn't respond
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_callback_query))

if __name__ == "__main__":
    try:
        # Set the bot app for the API
        set_bot_app(app)
        
        # Start API server in a separate thread
        api_thread = threading.Thread(target=run_api, daemon=True)
        api_thread.start()
        print(f"API server started on port {os.environ.get('TELEGRAM_BOT_API_PORT', 5000)}")
        
        # Run the bot in polling mode
        print("Starting bot in polling mode...")
        print("Bot will now handle messages without crashing...")
        app.run_polling()
    except Exception as e:
        print(f"Fatal error in main: {e}")
        print("Bot crashed. Please check the logs and restart.")

