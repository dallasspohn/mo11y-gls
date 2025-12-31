# Telegram Bot Quick Start

## ✅ Already Configured!

Your Telegram bot is already set up with:
- **Bot Token**: `7911694889:AAFBBOgJsP2iTR5WsKwryieqdNILuzpptCU`
- **User ID**: `7358003141`
- **Bot Name**: Alex Mercer (@memo_babe_bot)

## Quick Test

### 1. Test Bot Connection

```bash
# Verify bot token works
python3 << 'EOF'
import requests
token = "7911694889:AAFBBOgJsP2iTR5WsKwryieqdNILuzpptCU"
r = requests.get(f"https://api.telegram.org/bot{token}/getMe")
print("✅ Bot verified" if r.json().get('ok') else "❌ Failed")
print(f"Bot: @{r.json()['result']['username']}")
EOF
```

### 2. Send Test Message

```bash
python3 << 'EOF'
import requests
token = "7911694889:AAFBBOgJsP2iTR5WsKwryieqdNILuzpptCU"
user_id = 7358003141
url = f"https://api.telegram.org/bot{token}/sendMessage"
payload = {'chat_id': user_id, 'text': 'Test from Mo11y!'}
r = requests.post(url, json=payload)
print("✅ Sent" if r.json().get('ok') else "❌ Failed")
EOF
```

### 3. Run the Bot

**Option A: Direct Run (Testing)**
```bash
# Make sure Ollama is running
ollama ps

# Run the bot
python3 telegram_bot.py
```

**Option B: Systemd Service (Production)**
```bash
# Install service
sudo ./setup_telegram_bot.sh

# Check status
sudo systemctl status mo11y-telegram-bot.service

# View logs
sudo journalctl -u mo11y-telegram-bot.service -f
```

## What Happens

1. Bot starts and verifies token
2. Sends startup message to your Telegram
3. Listens for your messages
4. Processes messages through Alex Mercer persona
5. Sends responses back to Telegram

## Test It

1. **Start the bot** (see above)
2. **Open Telegram** and find your bot (@memo_babe_bot)
3. **Send a message**: "Hello Alex!"
4. **Wait for response** from Alex

## Troubleshooting

### Bot Not Responding?
- Check Ollama is running: `ollama ps`
- Check logs: `tail -f telegram_bot.log` or `journalctl -u mo11y-telegram-bot.service -f`
- Verify token: Run the test commands above

### Service Won't Start?
- Check service status: `sudo systemctl status mo11y-telegram-bot.service`
- Check logs: `sudo journalctl -u mo11y-telegram-bot.service -n 50`
- Verify paths in service file match your setup

### Messages Not Coming Through?
- Make sure you sent `/start` to the bot first
- Check user_id matches your Telegram ID
- Verify bot token is correct

## Files

- `telegram_bot.py` - Main bot code
- `telegram_bot_service.py` - Service wrapper
- `mo11y-telegram-bot.service` - Systemd service
- `setup_telegram_bot.sh` - Installation script
- `config.json` - Contains Telegram credentials

## Next Steps

1. ✅ Test message sending (done above)
2. ✅ Run bot manually to test
3. ✅ Install as service for production
4. ✅ Start chatting with Alex on Telegram!

---

**Ready to go!** Just run `python3 telegram_bot.py` and start chatting! 🚀
