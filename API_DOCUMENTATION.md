# Telegram Bot REST API Documentation

## Overview
This REST API allows you to send messages to users in specific channels of your Telegram bot. The bot uses a channel-based authentication system where users join channels using channel secrets, and you can send messages to all users in a specific channel.

## Authentication
All API endpoints require authentication using an API key. You can provide the API key in two ways:
- **Header**: `X-API-Key: your_api_key_here`
- **Query Parameter**: `?api_key=your_api_key_here`

## Channel System
- Users join channels using channel secrets (e.g., `/join welcome123`)
- Each channel has a unique name and secret
- You can send messages to all users in a specific channel
- Users can only be in one channel at a time

## Base URL
```
http://localhost:5000/api
```

## Endpoints

### 1. Health Check
**GET** `/api/health`

Check if the API is running and get basic statistics.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "authenticated_users": 5
}
```

### 2. Get All Users
**GET** `/api/users`

Get a list of all authenticated users.

**Headers:**
```
X-API-Key: your_api_key_here
```

**Response:**
```json
{
  "users": [
    {
      "user_id": 123456789,
      "username": "john_doe",
      "first_name": "John",
      "last_name": "Doe",
      "last_seen": "2024-01-01T12:00:00"
    }
  ],
  "total": 1
}
```

### 3. Broadcast to All Users
**POST** `/api/broadcast`

Send a message to all authenticated users.

**Headers:**
```
X-API-Key: your_api_key_here
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "Hello everyone! This is a broadcast message."
}
```

**Response:**
```json
{
  "message": "Broadcast completed",
  "total_users": 5,
  "sent_to": 4,
  "failed": 1,
  "failed_users": [
    {
      "user_id": 123456789,
      "username": "john_doe",
      "first_name": "John"
    }
  ]
}
```

### 4. Broadcast to Specific Channel
**POST** `/api/broadcast-to-channel`

Send a message to all users in a specific channel.

**Headers:**
```
X-API-Key: your_api_key_here
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "Hello channel members!",
  "channel": "announcements"
}
```

**Response:**
```json
{
  "message": "Broadcast to channel 'announcements' completed",
  "channel": "announcements",
  "channel_id": 1,
  "total_users": 5,
  "sent_to": 4,
  "failed": 1,
  "failed_users": [
    {
      "user_id": 123456789,
      "username": "john_doe",
      "first_name": "John"
    }
  ]
}
```

### 5. Get All Channels
**GET** `/api/channels`

Get a list of all available channels.

**Headers:**
```
X-API-Key: your_api_key_here
```

**Response:**
```json
{
  "channels": [
    {
      "channel_id": 1,
      "channel_name": "general",
      "description": "Default general channel",
      "is_active": true,
      "user_count": 5,
      "created_at": "2024-01-01T12:00:00"
    }
  ],
  "total": 1
}
```

### 6. Get Channel Users
**GET** `/api/channel/<channel_name>/users`

Get all users in a specific channel.

**Headers:**
```
X-API-Key: your_api_key_here
```

**Response:**
```json
{
  "channel": {
    "channel_id": 1,
    "channel_name": "general",
    "description": "Default general channel",
    "is_active": true
  },
  "users": [
    {
      "user_id": 123456789,
      "username": "john_doe",
      "first_name": "John",
      "last_name": "Doe",
      "last_seen": "2024-01-01T12:00:00"
    }
  ],
  "total": 1
}
```

### 7. Get Statistics
**GET** `/api/stats`

Get detailed bot statistics.

**Headers:**
```
X-API-Key: your_api_key_here
```

**Response:**
```json
{
  "total_users": 10,
  "authenticated_users": 7,
  "total_groups": 3,
  "total_channels": 2,
  "channel_distribution": {
    "general": 5,
    "announcements": 2
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

## Usage Examples

### Using curl

**Broadcast to all users:**
```bash
curl -X POST http://localhost:5000/api/broadcast \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello everyone!"}'
```

**Broadcast to specific channel:**
```bash
curl -X POST http://localhost:5000/api/broadcast-to-channel \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"message": "Channel members only!", "channel": "announcements"}'
```

**Get all channels:**
```bash
curl -X GET http://localhost:5000/api/channels \
  -H "X-API-Key: your_api_key_here"
```

**Get users in a channel:**
```bash
curl -X GET http://localhost:5000/api/channel/general/users \
  -H "X-API-Key: your_api_key_here"
```

**Get user list:**
```bash
curl -X GET http://localhost:5000/api/users \
  -H "X-API-Key: your_api_key_here"
```

### Using Python requests

```python
import requests

API_BASE = "http://localhost:5000/api"
API_KEY = "your_api_key_here"

headers = {"X-API-Key": API_KEY}

# Broadcast to all users
response = requests.post(
    f"{API_BASE}/broadcast",
    headers=headers,
    json={"message": "Hello from Python!"}
)
print(response.json())

# Broadcast to specific channel
response = requests.post(
    f"{API_BASE}/broadcast-to-channel",
    headers=headers,
    json={
        "message": "Channel message!",
        "channel": "announcements"
    }
)
print(response.json())

# Get all channels
response = requests.get(f"{API_BASE}/channels", headers=headers)
print(response.json())

# Get users in a channel
response = requests.get(f"{API_BASE}/channel/general/users", headers=headers)
print(response.json())
```

## Error Responses

### 401 Unauthorized
```json
{
  "error": "Unauthorized"
}
```

### 400 Bad Request
```json
{
  "error": "Message is required"
}
```

### 404 Not Found
```json
{
  "error": "No authenticated users found",
  "sent_to": 0
}
```

## Security Notes

1. **API Key**: Change the default API key in your `.env` file
2. **HTTPS**: Use HTTPS in production
3. **Rate Limiting**: Consider adding rate limiting for production use
4. **Firewall**: Restrict API access to trusted IPs if needed

## Configuration

Add these variables to your `.env` file:

```env
API_KEY=your_secure_api_key_here
API_PORT=5000
```

The API will start automatically when you run the bot.
