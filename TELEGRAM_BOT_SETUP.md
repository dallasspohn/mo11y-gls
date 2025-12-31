# Telegram Bot Setup - Alex Mercer Integration

## Overview

Connect Alex Mercer (or any persona) to Telegram so you can chat with your AI companion via Telegram!

## Quick Start

### Option 1: Run Directly (Testing)

```bash
# Set environment variables
export TELEGRAM_BOT_TOKEN="7911694889:AAFBBOgJsP2iTR5WsKwryieqdNILuzpptCU"
export TELEGRAM_USER_ID="7358003141"

# Run the bot
python3 telegram_bot.py
```

### Option 2: Run as Systemd Service (Production)

```bash
# Install and start the service
sudo ./setup_telegram_bot.sh
```

## Configuration

### Environment Variables

The bot uses these environment variables (already set in service file):
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `TELEGRAM_USER_ID`: Your Telegram user ID (chat ID)

### Config File

Credentials are also saved in `config.json`:
```json
{
  "telegram": {
    "bot_token": "7911694889:AAFBBOgJsP2iTR5WsKwryieqdNILuzpptCU",
    "user_id": "7358003141"
  }
}
```

## How It Works

1. **Bot Initialization**: Creates a Telegram bot using your bot token
2. **Agent Connection**: Connects to Mo11y agent with Alex Mercer persona
3. **Message Polling**: Continuously polls Telegram for new messages
4. **Message Processing**: Sends user messages to the agent
5. **Response Sending**: Sends agent responses back to Telegram

## Features

- ✅ **Persona Support**: Uses Alex Mercer persona (or configured persona)
- ✅ **Long Polling**: Efficient message polling
- ✅ **Message Splitting**: Automatically splits long messages (>4000 chars)
- ✅ **Error Handling**: Robust error handling and logging
- ✅ **User Filtering**: Only responds to messages from authorized user
- ✅ **Thread Support**: Maintains separate conversation threads per user

## Testing

### Test Bot Token

```bash
python3 << 'EOF'
import requests
token = "7911694889:AAFBBOgJsP2iTR5WsKwryieqdNILuzpptCU"
r = requests.get(f"https://api.telegram.org/bot{token}/getMe")
print("✅ Bot verified" if r.json().get('ok') else "❌ Bot failed")
print(r.json())
EOF
```

### Test Sending a Message

```bash
python3 << 'EOF'
import requests
token = "7911694889:AAFBBOgJsP2iTR5WsKwryieqdNILuzpptCU"
user_id = 7358003141
url = f"https://api.telegram.org/bot{token}/sendMessage"
payload = {'chat_id': user_id, 'text': 'Test message from Mo11y!'}
r = requests.post(url, json=payload)
print("✅ Message sent" if r.json().get('ok') else "❌ Failed")
EOF
```

### Run Bot Manually

```bash
# Make sure Ollama is running
ollama ps

# Run the bot
python3 telegram_bot.py
```

Then send a message to your bot on Telegram!

## Service Management

### Start/Stop Service

```bash
# Start
sudo systemctl start mo11y-telegram-bot.service

# Stop
sudo systemctl stop mo11y-telegram-bot.service

# Restart
sudo systemctl restart mo11y-telegram-bot.service

# Status
sudo systemctl status mo11y-telegram-bot.service
```

### View Logs

```bash
# Follow logs in real-time
sudo journalctl -u mo11y-telegram-bot.service -f

# View last 50 lines
sudo journalctl -u mo11y-telegram-bot.service -n 50

# View logs from file
tail -f telegram_bot.log
```

## Troubleshooting

### Bot Not Responding

1. **Check service status:**
   ```bash
   sudo systemctl status mo11y-telegram-bot.service
   ```

2. **Check logs:**
   ```bash
   sudo journalctl -u mo11y-telegram-bot.service -n 50
   ```

3. **Verify bot token:**
   ```bash
   python3 -c "import requests; r=requests.get('https://api.telegram.org/bot7911694889:AAFBBOgJsP2iTR5WsKwryieqdNILuzpptCU/getMe'); print(r.json())"
   ```

4. **Check Ollama is running:**
   ```bash
   ollama ps
   ```

### Bot Token Invalid

- Verify token is correct
- Check token hasn't been revoked
- Make sure bot is started (send `/start` to bot in Telegram)

### User ID Wrong

- Send a message to your bot
- Check logs for chat_id in received messages
- Update `TELEGRAM_USER_ID` in service file or config.json

### Agent Not Responding

- Check Ollama is running: `ollama ps`
- Check model is loaded: `ollama list | grep deepseek`
- Check logs for errors

## Files

- `telegram_bot.py` - Main Telegram bot implementation
- `telegram_bot_service.py` - Service wrapper for systemd
- `mo11y-telegram-bot.service` - Systemd service file
- `setup_telegram_bot.sh` - Installation script
- `config.json` - Configuration (includes Telegram credentials)

## Security Notes

⚠️ **Important**: 
- Bot token and user ID are stored in config.json and service file
- Keep these files secure
- Don't commit tokens to public repositories
- Consider using environment variables in production

## Next Steps

1. **Test the bot**: Send a message to your Telegram bot
2. **Check logs**: Monitor `telegram_bot.log` or journalctl
3. **Customize**: Modify persona or behavior as needed
4. **Add features**: Extend bot with additional commands or features

---

**Status**: ✅ Configured and ready to run
**Bot Token**: Set in config.json and service file
**User ID**: Set in config.json and service file
