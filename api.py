import os
import sqlite3
import threading
import time
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Environment variables are loaded by docker-compose

API_KEY = os.environ.get("API_KEY", "change-me")
API_PORT = int(os.environ.get("API_PORT", 5000))

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
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    print(f"Debug: Received API key: {api_key}, Expected: {API_KEY}")
    return api_key == API_KEY

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

@app.route('/api/broadcast-to-code', methods=['POST'])
def broadcast_to_auth_code():
    """Broadcast a message to users who authenticated with a specific code"""
    if not authenticate_api():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    
    if not data or 'message' not in data or 'auth_code' not in data:
        return jsonify({"error": "Message and auth_code are required"}), 400
    
    message = data['message']
    auth_code = data['auth_code']
    
    if not message.strip() or not auth_code.strip():
        return jsonify({"error": "Message and auth_code cannot be empty"}), 400
    
    # Get users with specific auth code
    conn = sqlite3.connect('data/bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, first_name, last_name, last_seen 
        FROM users 
        WHERE is_authenticated = TRUE AND auth_code = ?
    ''', (auth_code,))
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        return jsonify({
            "error": f"No users found with auth code: {auth_code}",
            "sent_to": 0
        }), 404
    
    # Send message to users with specific auth code
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
        "message": f"Broadcast to auth code '{auth_code}' completed",
        "auth_code": auth_code,
        "total_users": len(users),
        "sent_to": success_count,
        "failed": len(failed_users)
    }
    
    if failed_users:
        response["failed_users"] = failed_users
    
    return jsonify(response)

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
    
    # Get auth code distribution
    cursor.execute('''
        SELECT auth_code, COUNT(*) 
        FROM users 
        WHERE is_authenticated = TRUE AND auth_code IS NOT NULL
        GROUP BY auth_code
    ''')
    auth_codes = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        "total_users": total_users,
        "authenticated_users": auth_users,
        "total_groups": total_groups,
        "auth_code_distribution": {code: count for code, count in auth_codes},
        "timestamp": datetime.now().isoformat()
    })

def run_api():
    """Run the API server in a separate thread"""
    app.run(host='0.0.0.0', port=API_PORT, debug=False, use_reloader=False)

if __name__ == '__main__':
    run_api()
