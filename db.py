import os
import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional, Union

# Database configuration
DATABASE_PATH = 'data/bot_database.db'

def ensure_data_directory():
    """Create data directory if it doesn't exist"""
    os.makedirs('data', exist_ok=True)

def get_connection():
    """Get a database connection"""
    ensure_data_directory()
    return sqlite3.connect(DATABASE_PATH)

def init_database():
    """Initialize the database with all required tables"""
    ensure_data_directory()
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            is_authenticated BOOLEAN DEFAULT FALSE,
            channel_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
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
    
    # Create group_members table to track which users are in which groups
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_members (
            group_id INTEGER,
            user_id INTEGER,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (group_id, user_id),
            FOREIGN KEY (group_id) REFERENCES groups (group_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Create channels table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            channel_id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_name TEXT NOT NULL UNIQUE,
            channel_secret TEXT NOT NULL UNIQUE,
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_default_channel():
    """Create a default channel if none exists"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if any channels exist
    cursor.execute('SELECT COUNT(*) FROM channels')
    channel_count = cursor.fetchone()[0]
    
    if channel_count == 0:
        # Create a default channel
        cursor.execute('''
            INSERT INTO channels (channel_name, channel_secret, description, created_by)
            VALUES (?, ?, ?, ?)
        ''', ('general', 'welcome123', 'Default general channel for all users', 1))
        conn.commit()
        print("Created default channel 'general' with secret 'welcome123'")
    
    conn.close()

# User operations
def add_user_to_db(user_id: int, username: str, first_name: str, last_name: str):
    """Add or update a user in the database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, last_seen)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, username, first_name, last_name))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error in add_user_to_db: {e}")
        # Don't re-raise to prevent crashes

def get_user_auth_status(user_id: int) -> Tuple[bool, Optional[int]]:
    """Get user authentication status and channel ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT is_authenticated, channel_id FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return (result[0] if result else False, result[1] if result else None)

def get_user_channel_info(user_id: int) -> Optional[Tuple]:
    """Get user's channel information"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.is_authenticated, u.channel_id, c.channel_name, c.description
        FROM users u
        LEFT JOIN channels c ON u.channel_id = c.channel_id
        WHERE u.user_id = ?
    ''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def authenticate_user(user_id: int, channel_name: str, channel_secret: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Authenticate a user with both channel name and secret"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if both channel name and secret match and channel is active
    cursor.execute('''
        SELECT channel_id, channel_name, description 
        FROM channels 
        WHERE channel_name = ? AND channel_secret = ? AND is_active = TRUE
    ''', (channel_name, channel_secret))
    channel = cursor.fetchone()
    
    if channel:
        channel_id, channel_name_db, description = channel
        cursor.execute('''
            UPDATE users 
            SET is_authenticated = TRUE, channel_id = ?, last_seen = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (channel_id, user_id))
        conn.commit()
        conn.close()
        return True, channel_name_db, description
    conn.close()
    return False, None, None

def authenticate_user_legacy(user_id: int, channel_secret: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Legacy authentication with just channel secret (for backward compatibility)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if channel secret exists and is active
    cursor.execute('''
        SELECT channel_id, channel_name, description 
        FROM channels 
        WHERE channel_secret = ? AND is_active = TRUE
    ''', (channel_secret,))
    channel = cursor.fetchone()
    
    if channel:
        channel_id, channel_name, description = channel
        cursor.execute('''
            UPDATE users 
            SET is_authenticated = TRUE, channel_id = ?, last_seen = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (channel_id, user_id))
        conn.commit()
        conn.close()
        return True, channel_name, description
    conn.close()
    return False, None, None

def deauthenticate_user(user_id: int):
    """Remove user authentication and channel association"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET is_authenticated = FALSE, channel_id = NULL
        WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()

def get_authenticated_users() -> List[Tuple]:
    """Get all authenticated users from database"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, first_name, last_name, last_seen 
        FROM users 
        WHERE is_authenticated = TRUE
    ''')
    users = cursor.fetchall()
    conn.close()
    return users

def get_users_in_channel(channel_id: int) -> List[Tuple]:
    """Get all users in a specific channel"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, first_name, last_name, last_seen
        FROM users 
        WHERE channel_id = ? AND is_authenticated = TRUE
    ''', (channel_id,))
    results = cursor.fetchall()
    conn.close()
    return results

# Group operations
def add_group_to_db(group_id: int, group_title: str):
    """Add or update a group in the database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO groups (group_id, group_title, is_active)
            VALUES (?, ?, TRUE)
        ''', (group_id, group_title))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error in add_group_to_db: {e}")
        # Don't re-raise to prevent crashes

def add_user_to_group(group_id: int, user_id: int):
    """Add a user to a group in the group_members table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO group_members (group_id, user_id)
            VALUES (?, ?)
        ''', (group_id, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error in add_user_to_group: {e}")
        # Don't re-raise to prevent crashes

def remove_user_from_group(group_id: int, user_id: int):
    """Remove a user from a group in the group_members table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM group_members 
            WHERE group_id = ? AND user_id = ?
        ''', (group_id, user_id))
        conn.commit()
        conn.close()
        print(f"User {user_id} removed from group {group_id}")
    except Exception as e:
        print(f"Error in remove_user_from_group: {e}")
        # Don't re-raise to prevent crashes

# Channel operations
def create_channel(channel_name: str, channel_secret: str, description: str = "", created_by: int = 1) -> Tuple[bool, str]:
    """Create a new channel"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO channels (channel_name, channel_secret, description, created_by)
            VALUES (?, ?, ?, ?)
        ''', (channel_name, channel_secret, description, created_by))
        conn.commit()
        return True, "Channel created successfully"
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            # Don't reveal which field failed for security reasons
            return False, "Channel already exists"
        return False, f"Database error: {e}"
    except Exception as e:
        return False, f"Error creating channel: {e}"
    finally:
        conn.close()

def get_channel_by_secret(channel_secret: str) -> Optional[Tuple]:
    """Get channel information by secret"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT channel_id, channel_name, description, is_active
        FROM channels 
        WHERE channel_secret = ?
    ''', (channel_secret,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_channel_by_name(channel_name: str) -> Optional[Tuple]:
    """Get channel information by name"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT channel_id, channel_name, description, is_active
        FROM channels 
        WHERE channel_name = ? AND is_active = TRUE
    ''', (channel_name,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_all_channels() -> List[Tuple]:
    """Get all channels with user counts"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT channel_id, channel_name, description, is_active, created_at,
               (SELECT COUNT(*) FROM users WHERE channel_id = channels.channel_id AND is_authenticated = TRUE) as user_count
        FROM channels 
        ORDER BY created_at DESC
    ''')
    results = cursor.fetchall()
    conn.close()
    return results

def deactivate_channel(channel_name: str) -> Tuple[bool, str]:
    """Deactivate a channel (soft delete)"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if channel exists
        cursor.execute('SELECT channel_id, is_active FROM channels WHERE channel_name = ?', (channel_name,))
        channel = cursor.fetchone()
        
        if not channel:
            return False, f"Channel '{channel_name}' not found"
        
        channel_id, is_active = channel
        if not is_active:
            return False, f"Channel '{channel_name}' is already inactive"
        
        # Deactivate the channel
        cursor.execute('UPDATE channels SET is_active = FALSE WHERE channel_name = ?', (channel_name,))
        
        # Deauthenticate all users from this channel
        cursor.execute('''
            UPDATE users 
            SET is_authenticated = FALSE, channel_id = NULL 
            WHERE channel_id = ?
        ''', (channel_id,))
        
        conn.commit()
        return True, f"Channel '{channel_name}' deactivated successfully"
    except Exception as e:
        return False, f"Error deactivating channel: {e}"
    finally:
        conn.close()

def delete_channel(channel_name: str) -> Tuple[bool, str]:
    """Permanently delete a channel (hard delete)"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if channel exists
        cursor.execute('SELECT channel_id FROM channels WHERE channel_name = ?', (channel_name,))
        channel = cursor.fetchone()
        
        if not channel:
            return False, f"Channel '{channel_name}' not found"
        
        channel_id = channel[0]
        
        # Deauthenticate all users from this channel first
        cursor.execute('''
            UPDATE users 
            SET is_authenticated = FALSE, channel_id = NULL 
            WHERE channel_id = ?
        ''', (channel_id,))
        
        # Delete the channel
        cursor.execute('DELETE FROM channels WHERE channel_name = ?', (channel_name,))
        
        conn.commit()
        return True, f"Channel '{channel_name}' deleted permanently"
    except Exception as e:
        return False, f"Error deleting channel: {e}"
    finally:
        conn.close()

def reactivate_channel(channel_name: str) -> Tuple[bool, str]:
    """Reactivate a deactivated channel"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if channel exists
        cursor.execute('SELECT channel_id, is_active FROM channels WHERE channel_name = ?', (channel_name,))
        channel = cursor.fetchone()
        
        if not channel:
            return False, f"Channel '{channel_name}' not found"
        
        channel_id, is_active = channel
        if is_active:
            return False, f"Channel '{channel_name}' is already active"
        
        # Reactivate the channel
        cursor.execute('UPDATE channels SET is_active = TRUE WHERE channel_name = ?', (channel_name,))
        conn.commit()
        return True, f"Channel '{channel_name}' reactivated successfully"
    except Exception as e:
        return False, f"Error reactivating channel: {e}"
    finally:
        conn.close()

# Chat operations for API
def get_chats_with_authenticated_users() -> Tuple[List[Tuple], List[Tuple]]:
    """Get all chats (groups and private chats) where at least one user is authenticated"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all groups that have at least one authenticated user
    cursor.execute('''
        SELECT DISTINCT g.group_id, g.group_title, g.is_active
        FROM groups g
        INNER JOIN group_members gm ON g.group_id = gm.group_id
        INNER JOIN users u ON gm.user_id = u.user_id
        WHERE g.is_active = TRUE AND u.is_authenticated = TRUE
    ''')
    groups = cursor.fetchall()
    
    # Get all private chats (user_ids) that are authenticated
    cursor.execute('''
        SELECT DISTINCT user_id, username, first_name, last_name
        FROM users 
        WHERE is_authenticated = TRUE
    ''')
    private_chats = cursor.fetchall()
    
    conn.close()
    
    return groups, private_chats

def get_chats_in_channel(channel_id: int) -> Tuple[List[Tuple], List[Tuple]]:
    """Get all chats (groups and private chats) where users from a specific channel are present"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all groups that have at least one user from the specified channel
    cursor.execute('''
        SELECT DISTINCT g.group_id, g.group_title, g.is_active
        FROM groups g
        INNER JOIN group_members gm ON g.group_id = gm.group_id
        INNER JOIN users u ON gm.user_id = u.user_id
        WHERE g.is_active = TRUE AND u.channel_id = ? AND u.is_authenticated = TRUE
    ''', (channel_id,))
    groups = cursor.fetchall()
    
    # Get all private chats (user_ids) from the specified channel
    cursor.execute('''
        SELECT DISTINCT user_id, username, first_name, last_name
        FROM users 
        WHERE channel_id = ? AND is_authenticated = TRUE
    ''', (channel_id,))
    private_chats = cursor.fetchall()
    
    conn.close()
    
    return groups, private_chats

# Statistics operations
def get_bot_stats() -> dict:
    """Get comprehensive bot statistics"""
    conn = get_connection()
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
    
    return {
        "total_users": total_users,
        "authenticated_users": auth_users,
        "total_groups": total_groups,
        "total_channels": total_channels,
        "channel_distribution": channel_distribution
    }

def get_debug_info() -> dict:
    """Get debug information about groups and users"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all groups
    cursor.execute('SELECT group_id, group_title, is_active FROM groups ORDER BY created_at DESC')
    groups = cursor.fetchall()
    
    # Get all group members
    cursor.execute('''
        SELECT gm.group_id, g.group_title, gm.user_id, u.username, u.first_name, u.is_authenticated
        FROM group_members gm
        JOIN groups g ON gm.group_id = g.group_id
        JOIN users u ON gm.user_id = u.user_id
        ORDER BY gm.group_id, u.first_name
    ''')
    group_members = cursor.fetchall()
    
    # Get authenticated users
    cursor.execute('''
        SELECT user_id, username, first_name, last_name, is_authenticated, channel_id
        FROM users 
        WHERE is_authenticated = TRUE
        ORDER BY first_name
    ''')
    auth_users = cursor.fetchall()
    
    conn.close()
    
    return {
        "groups": groups,
        "group_members": group_members,
        "authenticated_users": auth_users
    }

# Standalone channel creation function for CLI usage
def create_channel_cli(channel_name: str, channel_secret: str, description: str = ""):
    """Create a new channel directly via CLI - initializes DB if needed"""
    # Initialize database first
    init_database()
    create_default_channel()
    
    success, message = create_channel(channel_name, channel_secret, description, 1)
    
    if success:
        print(f"✅ Channel '{channel_name}' created successfully!")
        print(f"   Secret: {channel_secret}")
        if description:
            print(f"   Description: {description}")
        return True
    else:
        if "Channel already exists" in message:
            print(f"❌ Channel '{channel_name}' already exists (name or secret conflict)")
        else:
            print(f"❌ {message}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Create channel:     python db.py create <channel_name> <channel_secret> [description]")
        print("  Deactivate channel: python db.py deactivate <channel_name>")
        print("  Delete channel:     python db.py delete <channel_name>")
        print("  Reactivate channel: python db.py reactivate <channel_name>")
        print("  List channels:      python db.py list")
        print("")
        print("Legacy create mode:   python db.py <channel_name> <channel_secret> [description]")
        print("")
        print("Examples:")
        print("  python db.py create testchannel secret123 'Test channel'")
        print("  python db.py deactivate testchannel")
        print("  python db.py delete testchannel")
        print("  python db.py list")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Initialize database first
    init_database()
    create_default_channel()
    
    if command == "create":
        if len(sys.argv) < 4:
            print("Usage: python db.py create <channel_name> <channel_secret> [description]")
            sys.exit(1)
        channel_name = sys.argv[2]
        channel_secret = sys.argv[3]
        description = sys.argv[4] if len(sys.argv) > 4 else ""
        create_channel_cli(channel_name, channel_secret, description)
    
    elif command == "deactivate":
        if len(sys.argv) < 3:
            print("Usage: python db.py deactivate <channel_name>")
            sys.exit(1)
        channel_name = sys.argv[2]
        success, message = deactivate_channel(channel_name)
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Usage: python db.py delete <channel_name>")
            sys.exit(1)
        channel_name = sys.argv[2]
        print(f"⚠️  WARNING: This will permanently delete channel '{channel_name}' and deauthenticate all users!")
        confirm = input("Are you sure? Type 'yes' to confirm: ")
        if confirm.lower() == 'yes':
            success, message = delete_channel(channel_name)
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
        else:
            print("❌ Operation cancelled")
    
    elif command == "reactivate":
        if len(sys.argv) < 3:
            print("Usage: python db.py reactivate <channel_name>")
            sys.exit(1)
        channel_name = sys.argv[2]
        success, message = reactivate_channel(channel_name)
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
    
    elif command == "list":
        channels = get_all_channels()
        if not channels:
            print("📺 No channels found.")
        else:
            print("📺 Available Channels:\n")
            for channel_id, channel_name, description, is_active, created_at, user_count in channels:
                status = "🟢 Active" if is_active else "🔴 Inactive"
                print(f"**{channel_name}** {status}")
                print(f"   ID: {channel_id} | Users: {user_count}")
                if description:
                    print(f"   Description: {description}")
                print(f"   Created: {created_at}\n")
    
    else:
        # Legacy mode - assume first arg is channel name for backward compatibility
        if len(sys.argv) < 3:
            print("Usage: python db.py <channel_name> <channel_secret> [description]")
            print("Example: python db.py testchannel secret123 'Test channel'")
            sys.exit(1)
        
        channel_name = sys.argv[1]
        channel_secret = sys.argv[2]
        description = sys.argv[3] if len(sys.argv) > 3 else ""
        create_channel_cli(channel_name, channel_secret, description)
