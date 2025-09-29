import os
# sqlite3 import no longer needed - using db.py
import threading
import time
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from db import (
    get_all_channels, get_bot_stats,
    get_authenticated_chats_for_channel, get_all_authenticated_chats
)

# Environment variables are loaded by docker-compose

TELEGRAM_BOT_API_KEY = os.environ.get("TELEGRAM_BOT_API_KEY", "change-me")
TELEGRAM_BOT_API_PORT = int(os.environ.get("TELEGRAM_BOT_API_PORT", 5000))
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variable to store the bot application (for compatibility)
bot_app = None

def set_bot_app(app_instance):
    """Set the bot application instance for sending messages"""
    global bot_app
    bot_app = app_instance

# All database functions are now imported from db.py

def send_message_to_chat(chat_id, message):
    """Send a message to a specific chat (group or private)"""
    # Get the bot token directly from environment (thread-safe)
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return False
    
    try:
        from telegram import Bot
        bot = Bot(token)
        
        # Try to get existing event loop first
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop exists, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the coroutine
        loop.run_until_complete(bot.send_message(chat_id=chat_id, text=message))
        return True
    except Exception as e:
        print(f"Error sending message to chat {chat_id}: {e}")
        return False

# Chat retrieval functions are now imported from db.py

def authenticate_api():
    """Check if the API request is authenticated"""
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    return api_key == TELEGRAM_BOT_API_KEY

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    stats = get_bot_stats()
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "total_authenticated_chats": stats['total_authenticated_chats']
    })


@app.route('/api/broadcast-to-channel', methods=['POST'])
def broadcast_to_channel():
    """Broadcast a message to chats where users from a specific channel are present"""
    if not authenticate_api():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    
    if not data or 'message' not in data or 'channel_name' not in data or 'channel_secret' not in data:
        return jsonify({"error": "Message, channel, and channel_secret are required"}), 400
    
    message = data['message']
    channel = data['channel_name']
    channel_secret = data['channel_secret']
    
    if not message.strip() or not channel.strip() or not channel_secret.strip():
        return jsonify({"error": "Message, channel, and channel_secret cannot be empty"}), 400
    
    # Get channel information by secret (for security)
    from db import get_channel_by_secret
    channel_info = get_channel_by_secret(channel_secret)
    if not channel_info:
        return jsonify({
            "error": "Invalid channel secret",
            "sent_to": 0
        }), 401
    
    channel_id, channel_name_from_db, description, is_active = channel_info
    
    # Verify the provided channel name matches the secret
    if channel_name_from_db != channel:
        return jsonify({
            "error": "Channel name does not match the provided secret",
            "sent_to": 0
        }), 401
    
    if not is_active:
        return jsonify({
            "error": f"Channel '{channel_name_from_db}' is inactive",
            "sent_to": 0
        }), 400
    
    # Get authenticated chats for this channel
    authenticated_chats = get_authenticated_chats_for_channel(channel_id)
    
    if not authenticated_chats:
        return jsonify({
            "error": f"No authenticated chats found for channel '{channel_name_from_db}'",
            "sent_to": 0
        }), 404
    
    # Send message to all authenticated chats
    success_count = 0
    failed_chats = []
    
    for chat_id, chat_type, chat_title, is_active, authenticated_at, last_activity in authenticated_chats:
        if send_message_to_chat(chat_id, message):
            success_count += 1
        else:
            failed_chats.append({
                "chat_id": chat_id,
                "chat_type": chat_type,
                "chat_title": chat_title
            })
    
    total_chats = len(authenticated_chats)
    
    response = {
        "message": f"Broadcast to channel '{channel_name_from_db}' completed",
        "channel": channel_name_from_db,
        "channel_id": channel_id,
        "total_authenticated_chats": total_chats,
        "sent_to": success_count,
        "failed": len(failed_chats)
    }
    
    if failed_chats:
        response["failed_chats"] = failed_chats
    
    return jsonify(response)

@app.route('/api/channels', methods=['GET'])
def get_channels():
    """Get all channels"""
    if not authenticate_api():
        return jsonify({"error": "Unauthorized"}), 401
    
    channels = get_all_channels()
    channel_list = []
    
    for channel in channels:
        channel_id, channel_name, description, is_active, created_at, user_count = channel
        channel_list.append({
            "channel_id": channel_id,
            "channel_name": channel_name,
            "description": description,
            "is_active": bool(is_active),
            "user_count": user_count,
            "created_at": created_at
        })
    
    return jsonify({
        "channels": channel_list,
        "total": len(channel_list)
    })

@app.route('/api/channel/<channel_name>/chats', methods=['POST'])
def get_channel_chats(channel_name):
    """Get authenticated chats for a specific channel - requires channel secret for security"""
    if not authenticate_api():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    if not data or 'channel_secret' not in data:
        return jsonify({"error": "channel_secret is required"}), 400
    
    channel_secret = data['channel_secret']
    if not channel_secret.strip():
        return jsonify({"error": "channel_secret cannot be empty"}), 400
    
    # Get channel information by secret (for security)
    from db import get_channel_by_secret
    channel_info = get_channel_by_secret(channel_secret)
    if not channel_info:
        return jsonify({"error": "Invalid channel secret"}), 401
    
    channel_id, channel_name_from_db, description, is_active = channel_info
    
    # Verify the provided channel name matches the secret
    if channel_name_from_db != channel_name:
        return jsonify({"error": "Channel name does not match the provided secret"}), 401
    
    if not is_active:
        return jsonify({"error": f"Channel '{channel_name_from_db}' is inactive"}), 400
    
    # Get authenticated chats for the channel
    chats = get_authenticated_chats_for_channel(channel_id)
    chat_list = []
    
    for chat in chats:
        chat_id, chat_type, chat_title, is_active, authenticated_at, last_activity = chat
        chat_list.append({
            "chat_id": chat_id,
            "chat_type": chat_type,
            "chat_title": chat_title,
            "is_active": bool(is_active),
            "authenticated_at": authenticated_at,
            "last_activity": last_activity
        })
    
    return jsonify({
        "channel": {
            "channel_id": channel_id,
            "channel_name": channel_name_from_db,
            "description": description,
            "is_active": bool(is_active)
        },
        "chats": chat_list,
        "total": len(chat_list)
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get bot statistics"""
    if not authenticate_api():
        return jsonify({"error": "Unauthorized"}), 401
    
    stats = get_bot_stats()
    total_users = stats['total_users']
    total_groups = stats['total_groups']
    total_channels = stats['total_channels']
    total_authenticated_chats = stats['total_authenticated_chats']
    channel_distribution = stats['channel_distribution']
    
    return jsonify({
        "total_users": total_users,
        "total_groups": total_groups,
        "total_channels": total_channels,
        "total_authenticated_chats": total_authenticated_chats,
        "channel_distribution": {name: count for name, count in channel_distribution},
        "timestamp": datetime.now().isoformat()
    })

def run_api():
    """Run the API server in a separate thread using Gunicorn for production"""
    import subprocess
    import sys
    
    # Use Gunicorn for production WSGI server
    cmd = [
        'gunicorn',
        '--bind', f'0.0.0.0:{TELEGRAM_BOT_API_PORT}',
        '--workers', '2',
        '--worker-class', 'sync',
        '--worker-connections', '1000',
        '--max-requests', '1000',
        '--max-requests-jitter', '100',
        '--timeout', '30',
        '--keep-alive', '2',
        '--preload',
        '--access-logfile', '-',
        '--error-logfile', '-',
        '--log-level', 'info',
        'api:app'
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting Gunicorn: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Shutting down API server...")
        sys.exit(0)

if __name__ == '__main__':
    run_api()
