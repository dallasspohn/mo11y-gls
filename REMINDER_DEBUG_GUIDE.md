# Reminder Service Debugging Guide

## Quick Test Commands

### 1. Add a test reminder (due in 2 minutes)
```bash
python3 process_reminders_now.py
```

### 2. Check reminder status
```bash
# Check database directly or use the reminder service
python3 -c "from reminder_service import ReminderService; rs = ReminderService(); print(rs.get_pending_reminders())"
```

### 3. Check if reminder service is running
```bash
systemctl status mo11y-reminder.service
```

### 4. View reminder service logs (real-time)
```bash
sudo journalctl -u mo11y-reminder.service -f
```

### 5. View recent logs
```bash
sudo journalctl -u mo11y-reminder.service --since "10 minutes ago" --no-pager
```

## Installing/Starting the Service

### Install the service
```bash
sudo cp mo11y-reminder.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mo11y-reminder.service
sudo systemctl start mo11y-reminder.service
```

### Check service status
```bash
systemctl status mo11y-reminder.service
```

### Restart service (after code changes)
```bash
sudo systemctl restart mo11y-reminder.service
```

## How Polling Works

1. **Check Interval**: Default is 60 seconds (configurable via `REMINDER_CHECK_INTERVAL` env var)
2. **Pending Reminders**: Only reminders where `reminder_time <= now` are considered pending
3. **Future Reminders**: Won't show as "pending" until their time arrives

## Debugging Steps

### Step 1: Verify reminders are in database
```bash
python3 -c "from reminder_service import ReminderService; rs = ReminderService(); print(rs.get_pending_reminders())"
```

### Step 2: Check if service is running
```bash
systemctl status mo11y-reminder.service
```

### Step 3: Check logs for polling activity
```bash
sudo journalctl -u mo11y-reminder.service --since "5 minutes ago" | grep -i "polling\|check\|reminder"
```

### Step 4: Verify Telegram credentials
The service looks for Telegram credentials in:
- `config.json` → `telegram.bot_token` and `telegram.user_id`
- Environment variables: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_USER_ID`

Check your config:
```bash
cat config.json | grep -A 3 telegram
```

### Step 5: Test Telegram notification manually
```python
python3 << 'EOF'
import requests
import json

with open('config.json') as f:
    config = json.load(f)

bot_token = config['telegram']['bot_token']
user_id = config['telegram']['user_id']

response = requests.post(
    f"https://api.telegram.org/bot{bot_token}/sendMessage",
    json={
        'chat_id': int(user_id),
        'text': 'Test notification from reminder service'
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
EOF
```

## Expected Log Output

When polling is working, you should see:
```
Polling check #1 - Checking for reminders...
No pending reminders found (check #1)
Sleeping for 60 seconds until next check...
```

When a reminder triggers:
```
🔔 Found 1 pending reminder(s)
📢 Processing reminder: Test Reminder (ID: 1) - Due: 2025-12-30T18:58:02
  → Sending Telegram notification...
  ✅ Telegram notification sent successfully
  → Checking for alarm.py...
  → Checking for ping.py...
  → Opening flashing webpage...
  → Marking reminder 1 as completed...
  ✅ Reminder 1 processed and marked complete
```

## Common Issues

### Issue: No Telegram notifications
- **Check**: Telegram credentials in config.json
- **Check**: Service logs for Telegram errors
- **Test**: Manual Telegram API call (see Step 5 above)

### Issue: Service not running
- **Check**: `systemctl status mo11y-reminder.service`
- **Fix**: Install and start service (see Installing section)

### Issue: Reminders not triggering
- **Check**: Reminder time is in the past or now
- **Check**: Reminder is not already completed
- **Check**: Service logs for errors

### Issue: Can't see polling activity
- **Check**: Logs show "Polling check #N" every minute (or configured interval)
- **Check**: Service is actually running
- **Check**: Database path is correct in service file
