import sqlite3
import sys

def create_channel(channel_name, channel_secret, description="", created_by=1):
    """Create a new channel directly in the database"""
    conn = sqlite3.connect('data/bot_database.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO channels (channel_name, channel_secret, description, created_by)
            VALUES (?, ?, ?, ?)
        ''', (channel_name, channel_secret, description, created_by))
        conn.commit()
        print(f"✅ Channel '{channel_name}' created successfully!")
        print(f"   Secret: {channel_secret}")
        print(f"   Description: {description}")
        return True
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            if "channel_name" in str(e):
                print(f"❌ Channel name '{channel_name}' already exists")
            else:
                print(f"❌ Channel secret '{channel_secret}' already exists")
        else:
            print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error creating channel: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_channel_db.py <channel_name> <channel_secret> [description]")
        print("Example: python create_channel_db.py testchannel secret123 'Test channel'")
        sys.exit(1)
    
    channel_name = sys.argv[1]
    channel_secret = sys.argv[2]
    description = sys.argv[3] if len(sys.argv) > 3 else ""
    
    create_channel(channel_name, channel_secret, description)
