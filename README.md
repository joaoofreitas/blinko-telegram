# Blinko Telegram Bot

A minimal Telegram bot for sending notes to your Blinko server.

> **Heads up:** Minor fix in progress. Everything else should work as expected.



## Quick Start with Docker Compose

1. **Clone and configure**:
   ```bash
   git clone <repository-url>
   cd blinko-telegram
   cp .env.example .env
   ```

2. **Edit `.env` file**:
   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   BLINKO_BASE_URL=https://your-blinko-instance.com/api/v1
   ENCRYPTION_KEY=your_32_byte_encryption_key_here
   ```

3. **Generate encryption key** (optional but recommended):
   ```bash
   # Method 1: Using the included script
   python3 generate_key.py
   
   # Method 2: One-liner
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

4. **Start with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

## Manual Setup

1. **Install dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your BOT_TOKEN and BLINKO_BASE_URL
   ```

3. **Start the bot**:
   ```bash
   python3 bot.py
   ```

## Commands

| Command | Description |
|---------|-------------|
| `/configure <token>` | Set your Blinko API token |
| `/note <text>` | Create a note |
| `/blinko <text>` | Create a blinko |
| `/status` | Check configuration |
| `/reset` | Remove configuration |

## Features

- **Reply to Update**: Reply to your own `/note` or `/blinko` messages to update them
- **Secure Storage**: API tokens are encrypted before storage
- **Simple Commands**: Clean, user-friendly command interface
- **Docker Support**: Easy deployment with Docker Compose

## Configuration

### Telegram Bot Token
Get your bot token from [@BotFather](https://t.me/BotFather).

### Environment Variables
```env
BOT_TOKEN=your_telegram_bot_token_here
BLINKO_BASE_URL=https://your-blinko-instance.com/api/v1
ENCRYPTION_KEY=your_32_byte_encryption_key_here  # optional, auto-generated if not provided
DATABASE_PATH=./bot_data.db  # optional, defaults to ./bot_data.db
```

### Encryption Key Generation
For production use, generate a secure 32-byte encryption key:

```bash
# Method 1: Using the included script
python3 generate_key.py

# Method 2: Using Python one-liner
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Method 3: Using OpenSSL
openssl rand -base64 32
```

## Docker Deployment

### Using Docker Compose (Recommended)
```bash
# Start the bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

### Data Persistence
The bot data is stored in `./data/bot_data.db` which is mounted as a volume in Docker.

## Files

- `bot.py` - Main bot logic with reply-to-update functionality
- `blinko_api.py` - Blinko API client with create/update support
- `storage.py` - Encrypted token storage and message tracking
- `generate_key.py` - Utility script to generate encryption keys
- `docker-compose.yml` - Docker Compose configuration
- `Dockerfile` - Docker image definition
- `requirements.txt` - Python dependencies

## Security

- API tokens are encrypted using Fernet (symmetric encryption)
- Bot runs as non-root user in Docker
- SSL verification disabled for self-signed certificates (configurable)
- No sensitive data in logs
