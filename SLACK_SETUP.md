# Slack Bot Setup - Mo11y Integration

Connect Mo11y (or any persona) to Slack so you can chat with your AI companion via Slack!

## Quick Start

### Prerequisites

- Slack workspace with admin access
- Bot token from Slack API

### Setup Steps

1. **Create a Slack App**
   - Go to https://api.slack.com/apps
   - Click "Create New App" → "From scratch"
   - Name your app (e.g., "Mo11y Bot")
   - Select your workspace

2. **Configure Bot Token Scopes**
   - Go to "OAuth & Permissions" in the sidebar
   - Add the following Bot Token Scopes:
     - `chat:write` - Send messages
     - `channels:history` - Read channel messages (if using channels)
     - `groups:history` - Read private channel messages
     - `im:history` - Read direct messages
     - `mpim:history` - Read group direct messages

3. **Install App to Workspace**
   - Scroll to "Install App to Workspace"
   - Click and authorize
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)

4. **Get Channel ID or User ID**
   - For a channel: Right-click channel → "View channel details" → Copy Channel ID
   - For DM: Use your user ID (found in your Slack profile)
   - Or use the channel name (e.g., `#general`)

5. **Configure Mo11y**
   
   Add to your `config.json`:
   ```json
   {
     "slack": {
       "bot_token": "xoxb-your-bot-token-here",
       "channel_id": "C1234567890"
     }
   }
   ```
   
   Or use environment variables:
   ```bash
   export SLACK_BOT_TOKEN="xoxb-your-bot-token-here"
   export SLACK_CHANNEL_ID="C1234567890"
   ```

6. **Run the Bot**
   ```bash
   python3 slack_bot.py
   ```

   Or as a systemd service:
   ```bash
   sudo cp mo11y-slack-bot.service /etc/systemd/system/
   sudo systemctl enable mo11y-slack-bot.service
   sudo systemctl start mo11y-slack-bot.service
   ```

## Configuration Options

### Using Channel ID
```json
{
  "slack": {
    "bot_token": "xoxb-...",
    "channel_id": "C1234567890"
  }
}
```

### Using User ID (DM)
```json
{
  "slack": {
    "bot_token": "xoxb-...",
    "user_id": "U1234567890"
  }
}
```

### Environment Variables
```bash
export SLACK_BOT_TOKEN="xoxb-your-token"
export SLACK_CHANNEL_ID="C1234567890"
# OR
export SLACK_USER_ID="U1234567890"
```

## Optional: Telegram Fallback

Mo11y supports Telegram as an optional alternative. If Slack is not configured, the system will automatically fall back to Telegram if configured:

```json
{
  "slack": {
    "bot_token": "xoxb-...",
    "channel_id": "C1234567890"
  },
  "telegram": {
    "bot_token": "optional-telegram-token",
    "user_id": "optional-telegram-user-id"
  }
}
```

The reminder service will try Slack first, then fall back to Telegram if Slack is not available.

## Troubleshooting

### Bot not responding
- Check bot token is correct (starts with `xoxb-`)
- Verify channel ID is correct
- Check bot has been added to the channel (if using channels)
- Check logs: `tail -f slack_bot.log`

### Permission errors
- Ensure bot has `chat:write` scope
- Ensure bot is added to the channel
- Check bot token hasn't expired

### Service not starting
```bash
# Check service status
sudo systemctl status mo11y-slack-bot.service

# View logs
sudo journalctl -u mo11y-slack-bot.service -f

# Check configuration
python3 -c "import json; print(json.load(open('config.json')).get('slack', {}))"
```

## Features

- **Real-time Messaging**: Chat with Mo11y via Slack
- **Persona Support**: Works with any configured persona
- **Thread Support**: Replies are threaded for better organization
- **Long Messages**: Automatically splits long responses
- **Memory Integration**: All conversations are stored in Mo11y's memory system

## Notes

- Slack has a 4000 character limit per message (Mo11y automatically splits longer messages)
- Bot must be added to channels to read messages
- For DMs, use `user_id` instead of `channel_id`
- Bot token should be kept secure (don't commit to git)

---

**Note**: Telegram is also supported as an optional alternative. See `TELEGRAM_BOT_SETUP.md` for Telegram configuration.
