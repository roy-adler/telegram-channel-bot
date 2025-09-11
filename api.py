import os
import sqlite3
import threading
import time
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Environment variables are loaded by docker-compose

TELEGRAM_BOT_API_KEY = os.environ.get("TELEGRAM_BOT_API_KEY", "change-me")
TELEGRAM_BOT_API_PORT
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variable to store the bot application
bot_app = None

def set_bot_app(app_instance):
    """Set the bot application instance for sending messages"""
    global bot_app
    bot_app = app_instance

def get_authenticated_users():
    """Get all authenticated users from database"""
    conn = sqlite3.connect('data/bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, first_name, last_name, last_seen 
        FROM users 
        WHERE is_authenticated = TRUE
    ''')
    users = cursor.fetchall()
    conn.close()
    return users

def get_users_in_channel(channel_id):
    """Get all users in a specific channel"""
    conn = sqlite3.connect('data/bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, first_name, last_name, last_seen
        FROM users 
        WHERE channel_id = ? AND is_authenticated = TRUE
    ''', (channel_id,))
    users = cursor.fetchall()
    conn.close()
    return users

def get_channel_by_name(channel_name):
    """Get channel information by name"""
    conn = sqlite3.connect('data/bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT channel_id, channel_name, description, is_active
        FROM channels 
        WHERE channel_name = ? AND is_active = TRUE
    ''', (channel_name,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_all_channels():
    """Get all channels with user counts"""
    conn = sqlite3.connect('data/bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.channel_id, c.channel_name, c.description, c.is_active, c.created_at,
               (SELECT COUNT(*) FROM users WHERE channel_id = c.channel_id AND is_authenticated = TRUE) as user_count
        FROM channels c
        ORDER BY c.created_at DESC
    ''')
    results = cursor.fetchall()
    conn.close()
    return results

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

def authenticate_api():
    """Check if the API request is authenticated"""
    TELEGRAM_BOT_API_KEY = request.headers.get('X-API-Key') or request.args.get('TELEGRAM_BOT_API_KEY')
    print(f"Debug: Received API key: {TELEGRAM_BOT_API_KEY}, Expected: {TELEGRAM_BOT_API_KEY}")
    return TELEGRAM_BOT_API_KEY == TELEGRAM_BOT_API_KEY

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
    """Broadcast a message to all authenticated users"""
    if not authenticate_api():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({"error": "Message is required"}), 400
    
    message = data['message']
    if not message.strip():
        return jsonify({"error": "Message cannot be empty"}), 400
    
    # Get all authenticated users
    users = get_authenticated_users()
    
    if not users:
        return jsonify({
            "error": "No authenticated users found",
            "sent_to": 0
        }), 404
    
    # Send message to all users
    success_count = 0
    failed_users = []
    
    for user in users:
        user_id = user[0]
        if send_message_to_user(user_id, message):
            success_count += 1
        else:
            failed_users.append({
                "user_id": user_id,
                "username": user[1],
                "first_name": user[2]
            })
    
    response = {
        "message": "Broadcast completed",
        "total_users": len(users),
        "sent_to": success_count,
        "failed": len(failed_users)
    }
    
    if failed_users:
        response["failed_users"] = failed_users
    
    return jsonify(response)

@app.route('/api/broadcast-to-channel', methods=['POST'])
def broadcast_to_channel():
    """Broadcast a message to users in a specific channel"""
    if not authenticate_api():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    
    if not data or 'message' not in data or 'channel' not in data:
        return jsonify({"error": "Message and channel are required"}), 400
    
    message = data['message']
    channel = data['channel']
    
    if not message.strip() or not channel.strip():
        return jsonify({"error": "Message and channel cannot be empty"}), 400
    
    # Get channel information
    channel_info = get_channel_by_name(channel)
    if not channel_info:
        return jsonify({
            "error": f"Channel '{channel}' not found",
            "sent_to": 0
        }), 404
    
    channel_id, channel_name, description, is_active = channel_info
    
    if not is_active:
        return jsonify({
            "error": f"Channel '{channel_name}' is inactive",
            "sent_to": 0
        }), 400
    
    # Get users in the channel
    users = get_users_in_channel(channel_id)
    
    if not users:
        return jsonify({
            "error": f"No users found in channel '{channel_name}'",
            "sent_to": 0
        }), 404
    
    # Send message to users in the channel
    success_count = 0
    failed_users = []
    
    for user in users:
        user_id = user[0]
        if send_message_to_user(user_id, message):
            success_count += 1
        else:
            failed_users.append({
                "user_id": user_id,
                "username": user[1],
                "first_name": user[2]
            })
    
    response = {
        "message": f"Broadcast to channel '{channel_name}' completed",
        "channel": channel_name,
        "channel_id": channel_id,
        "total_users": len(users),
        "sent_to": success_count,
        "failed": len(failed_users)
    }
    
    if failed_users:
        response["failed_users"] = failed_users
    
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

@app.route('/api/channel/<channel_name>/users', methods=['GET'])
def get_channel_users(channel_name):
    """Get users in a specific channel"""
    if not authenticate_api():
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get channel information
    channel_info = get_channel_by_name(channel_name)
    if not channel_info:
        return jsonify({"error": f"Channel '{channel_name}' not found"}), 404
    
    channel_id, channel_name, description, is_active = channel_info
    
    if not is_active:
        return jsonify({"error": f"Channel '{channel_name}' is inactive"}), 400
    
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
            "channel_name": channel_name,
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
    
    conn = sqlite3.connect('data/bot_database.db')
    cursor = conn.cursor()
    
    # Get user stats
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_authenticated = TRUE')
    auth_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM groups')
    total_groups = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM channels')
    total_channels = cursor.fetchone()[0]
    
    # Get channel distribution
    cursor.execute('''
        SELECT c.channel_name, COUNT(u.user_id) as user_count
        FROM channels c
        LEFT JOIN users u ON c.channel_id = u.channel_id AND u.is_authenticated = TRUE
        GROUP BY c.channel_id, c.channel_name
        ORDER BY user_count DESC
    ''')
    channel_distribution = cursor.fetchall()
    
    conn.close()
    
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
