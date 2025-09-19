import os
# sqlite3 import no longer needed - using db.py
import threading
import time
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from db import (
    get_authenticated_users, get_users_in_channel, get_channel_by_name,
    get_all_channels, get_chats_with_authenticated_users, get_chats_in_channel,
    get_bot_stats
)

# Environment variables are loaded by docker-compose

TELEGRAM_BOT_API_KEY = os.environ.get("TELEGRAM_BOT_API_KEY", "change-me")
TELEGRAM_BOT_API_PORT = int(os.environ.get("TELEGRAM_BOT_API_PORT", 5000))
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variable to store the bot application
bot_app = None

def set_bot_app(app_instance):
    """Set the bot application instance for sending messages"""
    global bot_app
    bot_app = app_instance

# All database functions are now imported from db.py

def send_message_to_user(user_id, message):
    """Send a message to a specific user"""
    if bot_app:
        try:
            # Use asyncio to run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bot_app.bot.send_message(chat_id=user_id, text=message))
            loop.close()
            return True
        except Exception as e:
            print(f"Error sending message to user {user_id}: {e}")
            return False
    return False

def send_message_to_chat(chat_id, message):
    """Send a message to a specific chat (group or private)"""
    if bot_app:
        try:
            # Use asyncio to run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bot_app.bot.send_message(chat_id=chat_id, text=message))
            loop.close()
            return True
        except Exception as e:
            print(f"Error sending message to chat {chat_id}: {e}")
            return False
    return False

# Chat retrieval functions are now imported from db.py

def authenticate_api():
    """Check if the API request is authenticated"""
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    print(f"Debug: Received API key: {api_key}, Expected: {TELEGRAM_BOT_API_KEY}")
    return api_key == TELEGRAM_BOT_API_KEY

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "authenticated_users": len(get_authenticated_users())
    })

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all authenticated users"""
    if not authenticate_api():
        return jsonify({"error": "Unauthorized"}), 401
    
    users = get_authenticated_users()
    user_list = []
    
    for user in users:
        user_list.append({
            "user_id": user[0],
            "username": user[1],
            "first_name": user[2],
            "last_name": user[3],
            "last_seen": user[4]
        })
    
    return jsonify({
        "users": user_list,
        "total": len(user_list)
    })

@app.route('/api/broadcast', methods=['POST'])
def broadcast_message():
    """Broadcast a message to all chats where authenticated users are present"""
    if not authenticate_api():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({"error": "Message is required"}), 400
    
    message = data['message']
    if not message.strip():
        return jsonify({"error": "Message cannot be empty"}), 400
    
    # Get all chats with authenticated users
    groups, private_chats = get_chats_with_authenticated_users()
    
    if not groups and not private_chats:
        return jsonify({
            "error": "No chats with authenticated users found",
            "sent_to": 0
        }), 404
    
    # Send message to all chats
    success_count = 0
    failed_chats = []
    
    # Send to groups
    for group_id, group_title, is_active in groups:
        if send_message_to_chat(group_id, message):
            success_count += 1
        else:
            failed_chats.append({
                "chat_id": group_id,
                "chat_type": "group",
                "chat_title": group_title
            })
    
    # Send to private chats
    for user_id, username, first_name, last_name in private_chats:
        if send_message_to_chat(user_id, message):
            success_count += 1
        else:
            failed_chats.append({
                "chat_id": user_id,
                "chat_type": "private",
                "username": username,
                "first_name": first_name,
                "last_name": last_name
            })
    
    total_chats = len(groups) + len(private_chats)
    
    response = {
        "message": "Broadcast completed",
        "total_chats": total_chats,
        "groups": len(groups),
        "private_chats": len(private_chats),
        "sent_to": success_count,
        "failed": len(failed_chats)
    }
    
    if failed_chats:
        response["failed_chats"] = failed_chats
    
    return jsonify(response)

@app.route('/api/broadcast-to-channel', methods=['POST'])
def broadcast_to_channel():
    """Broadcast a message to chats where users from a specific channel are present"""
    if not authenticate_api():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    
    if not data or 'message' not in data or 'channel' not in data or 'channel_secret' not in data:
        return jsonify({"error": "Message, channel, and channel_secret are required"}), 400
    
    message = data['message']
    channel = data['channel']
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
    
    # Get chats where users from this channel are present
    groups, private_chats = get_chats_in_channel(channel_id)
    
    if not groups and not private_chats:
        return jsonify({
            "error": f"No chats found with users from channel '{channel_name_from_db}'",
            "sent_to": 0
        }), 404
    
    # Send message to all chats
    success_count = 0
    failed_chats = []
    
    # Send to groups
    for group_id, group_title, is_active in groups:
        if send_message_to_chat(group_id, message):
            success_count += 1
        else:
            failed_chats.append({
                "chat_id": group_id,
                "chat_type": "group",
                "chat_title": group_title
            })
    
    # Send to private chats
    for user_id, username, first_name, last_name in private_chats:
        if send_message_to_chat(user_id, message):
            success_count += 1
        else:
            failed_chats.append({
                "chat_id": user_id,
                "chat_type": "private",
                "username": username,
                "first_name": first_name,
                "last_name": last_name
            })
    
    total_chats = len(groups) + len(private_chats)
    
    response = {
        "message": f"Broadcast to channel '{channel_name_from_db}' completed",
        "channel": channel_name_from_db,
        "channel_id": channel_id,
        "total_chats": total_chats,
        "groups": len(groups),
        "private_chats": len(private_chats),
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

@app.route('/api/channel/<channel_name>/users', methods=['POST'])
def get_channel_users(channel_name):
    """Get users in a specific channel - requires channel secret for security"""
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
    
    # Get users in the channel
    users = get_users_in_channel(channel_id)
    user_list = []
    
    for user in users:
        user_id, username, first_name, last_name, last_seen = user
        user_list.append({
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "last_seen": last_seen
        })
    
    return jsonify({
        "channel": {
            "channel_id": channel_id,
            "channel_name": channel_name_from_db,
            "description": description,
            "is_active": bool(is_active)
        },
        "users": user_list,
        "total": len(user_list)
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get bot statistics"""
    if not authenticate_api():
        return jsonify({"error": "Unauthorized"}), 401
    
    stats = get_bot_stats()
    total_users = stats['total_users']
    auth_users = stats['authenticated_users']
    total_groups = stats['total_groups']
    total_channels = stats['total_channels']
    channel_distribution = stats['channel_distribution']
    
    return jsonify({
        "total_users": total_users,
        "authenticated_users": auth_users,
        "total_groups": total_groups,
        "total_channels": total_channels,
        "channel_distribution": {name: count for name, count in channel_distribution},
        "timestamp": datetime.now().isoformat()
    })

def run_api():
    """Run the API server in a separate thread"""
    app.run(host='0.0.0.0', port=TELEGRAM_BOT_API_PORT, debug=False, use_reloader=False)

if __name__ == '__main__':
    run_api()
