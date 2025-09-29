# Telegram Channel Bot Docker Setup

This project contains a Telegram channel bot that runs using Docker Compose. The bot allows you to send broadcast messages to authenticated chats (groups and private chats) that have joined specific channels.

## Setup Instructions

1. **Create a `.env` file** in the project root with the following variables:
   ```bash
   # Copy from env.example and update with your values
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_BOT_API_URL=api.telegram.org
   TELEGRAM_BOT_PUBLIC_URL=https://yourdomain.com
   TELEGRAM_BOT_SECRET_TOKEN=your_secret_token_here
   ```

2. **Get your bot token**:
   - Message @BotFather on Telegram
   - Create a new bot with `/newbot`
   - Copy the token provided

3. **Set up your public URL**:
   - You need a publicly accessible HTTPS URL for webhooks
   - This could be your domain with a reverse proxy (nginx, traefik, etc.)
   - Or use a service like ngrok for testing: `ngrok http 8080`

4. **Run the bot**:
   ```bash
   # Build and start the bot
   docker-compose up --build

   # Run in detached mode
   docker-compose up -d --build

   # View logs
   docker-compose logs -f telegram-channel-bot

   # Stop the bot
   docker-compose down
   ```

## How It Works

The bot uses a **chat-based authentication system**:

1. **Join a Channel**: Users can use `/join <channel_name> <channel_secret>` in any chat (group or private) to authenticate that chat for a specific channel
2. **Broadcast Messages**: Administrators can send broadcast messages via the API to all authenticated chats for a channel
3. **Chat Management**: Each chat can only be authenticated for one channel at a time

## Bot Commands

### User Commands
- `/start` - Start the bot and see welcome message
- `/join <channel_name> <channel_secret>` - Authenticate this chat for a channel
- `/leave` - Remove this chat from the current channel
- `/status` - Check if this chat is authenticated for any channel
- `/register` - Register in a group (for group chats)
- `/stop` - Remove chat authentication and user from group

### Admin Commands (Admin only)
- `/stats` - View bot statistics including authenticated chats
- `/create <channel_name> <channel_secret> [description]` - Create a new channel
- `/list_channels` - List all available channels
- `/channel_users <channel_id>` - List users in a specific channel
- `/debug_groups` - Debug group and user tracking information

## API Endpoints

The bot provides REST API endpoints for sending broadcasts:

- `POST /api/broadcast-to-channel` - Send a message to all authenticated chats for a channel
- `GET /api/health` - Health check endpoint
- `GET /api/users` - Get all authenticated users
- `GET /api/channels` - Get all channels
- `GET /api/stats` - Get bot statistics

### Example API Usage

```bash
curl -X POST http://localhost:5000/api/broadcast-to-channel \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "message": "Hello from the bot!",
    "channel_name": "general",
    "channel_secret": "welcome123"
  }'
```

## Environment Variables

- `TELEGRAM_BOT_TOKEN`: Your bot token from @BotFather
- `ADMIN_USER_ID`: Your Telegram user ID (for admin commands)
- `TELEGRAM_BOT_API_KEY`: API key for REST API authentication
- `TELEGRAM_BOT_API_PORT`: Port for the API server (default: 5000)

## Usage Examples

### Setting Up a Channel

1. **Create a channel** (admin only):
   ```
   /create announcements secret123 This is for important announcements
   ```

2. **Users join the channel** in their groups or private chats:
   ```
   /join announcements secret123
   ```

3. **Send broadcasts** via API:
   ```bash
   curl -X POST http://localhost:5000/api/broadcast-to-channel \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your_api_key" \
     -d '{
       "message": "Important announcement!",
       "channel_name": "announcements",
       "channel_secret": "secret123"
     }'
   ```

### Chat-Based Authentication

- **In a Group**: When someone uses `/join` in a group, the entire group becomes authenticated for that channel
- **In Private Chat**: When someone uses `/join` in a private chat, that private chat becomes authenticated
- **One Channel Per Chat**: Each chat can only be authenticated for one channel at a time
- **Switch Channels**: If a chat is already authenticated and someone uses `/join` with a different channel, it switches to the new channel

## Testing with ngrok

For local testing, you can use ngrok:

1. Install ngrok: https://ngrok.com/
2. Run: `ngrok http 5000` (note: port 5000 for API, not 8080)
3. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)
4. Set `TELEGRAM_BOT_PUBLIC_URL=https://abc123.ngrok.io` in your `.env` file
5. Run `docker-compose up --build`

## Health Check

The bot includes a health check that verifies the service is running properly:

```bash
curl http://localhost:5000/api/health
```

## Database

The bot uses SQLite database with the following key tables:
- `channels` - Stores channel information
- `authenticated_chats` - Tracks which chats are authenticated for which channels
- `users` - User information
- `groups` - Group information
- `group_members` - User-group relationships
