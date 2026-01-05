#!/usr/bin/env python3
"""
Manually process pending reminders right now
Useful for testing when service isn't running
"""

import json
import os
import sys
from datetime import datetime
from reminder_service import ReminderService, send_slack_notification, trigger_alarm_script, trigger_ping_script, open_flashing_webpage

# Get database path from config
config_path = "config.json"
db_path = "mo11y_companion.db"

if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
        db_path = config.get("db_path", "mo11y_companion.db")

print(f"Using database: {db_path}")
print(f"Current time: {datetime.now().isoformat()}\n")

# Initialize service
service = ReminderService(db_path)

# Get pending reminders
pending = service.get_pending_reminders()

if not pending:
    print("✅ No pending reminders found")
    sys.exit(0)

print(f"🔔 Found {len(pending)} pending reminder(s)\n")

for reminder in pending:
    reminder_id = reminder.get('id')
    title = reminder.get('title', 'Untitled')
    description = reminder.get('description', '')
    reminder_time = reminder.get('reminder_time', 'Unknown time')
    
    print(f"📢 Processing reminder: {title} (ID: {reminder_id})")
    print(f"   Due: {reminder_time}\n")
    
    # Send Slack notification (with optional Telegram fallback)
    print("  → Sending Slack notification...")
    try:
        success = send_slack_notification(title, description, reminder_time, db_path)
        if success:
            print("  ✅ Slack notification sent successfully")
        else:
            print("  ❌ Slack notification failed")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Trigger alarm.py if it exists
    print("  → Checking for alarm.py...")
    try:
        trigger_alarm_script(title, description)
    except Exception as e:
        print(f"  ⚠️  Could not trigger alarm script: {e}")
    
    # Trigger ping.py if it exists
    print("  → Checking for ping.py...")
    try:
        trigger_ping_script(title, description)
    except Exception as e:
        print(f"  ⚠️  Could not trigger ping script: {e}")
    
    # Open flashing webpage
    print("  → Opening flashing webpage...")
    try:
        open_flashing_webpage(title, description)
    except Exception as e:
        print(f"  ⚠️  Could not open flashing webpage: {e}")
    
    # Mark reminder as completed
    print("  → Marking reminder as completed...")
    service.mark_completed(reminder_id)
    print(f"  ✅ Reminder {reminder_id} processed and marked complete\n")

print("✅ All reminders processed!")
