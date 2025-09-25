# Telegram Channel Bot Docker Setup

This project contains a Telegram channel bot that runs using Docker Compose.

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

## Environment Variables

- `TELEGRAM_BOT_TOKEN`: Your bot token from @BotFather
- `TELEGRAM_BOT_API_URL`: Telegram API URL (usually `api.telegram.org`)
- `TELEGRAM_BOT_PUBLIC_URL`: Public HTTPS URL where webhooks will be received
- `TELEGRAM_BOT_SECRET_TOKEN`: Secret token for webhook verification (optional)

## Testing with ngrok

For local testing, you can use ngrok:

1. Install ngrok: https://ngrok.com/
2. Run: `ngrok http 8080`
3. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)
4. Set `TELEGRAM_BOT_PUBLIC_URL=https://abc123.ngrok.io` in your `.env` file
5. Run `docker-compose up --build`

## Health Check

The bot includes a health check that verifies the service is running properly.
