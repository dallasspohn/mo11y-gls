"""
Reminder Service
Manages reminders and notifications
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3
import os
import time
import logging
import sys
import subprocess
import requests
import json
import webbrowser

# Setup logging for module-level functions
# Create logger that will be configured in main() but available for functions
logger = logging.getLogger(__name__)
# Set a default handler if none exists (for when used as module)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


class ReminderService:
    """Manages reminders"""
    
    def __init__(self, db_path: str = "mo11y_companion.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize reminders database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                reminder_time DATETIME NOT NULL,
                completed BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_reminder(self, title: str, reminder_time: datetime,
                    description: Optional[str] = None) -> int:
        """Add a reminder
        
        Returns:
            int: The ID of the created reminder
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO reminders
            (title, description, reminder_time)
            VALUES (?, ?, ?)
        """, (title, description, reminder_time.isoformat()))
        
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return reminder_id
    
    def get_pending_reminders(self) -> List[Dict]:
        """Get pending reminders"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM reminders
            WHERE completed = 0 AND reminder_time <= ?
            ORDER BY reminder_time
        """, (datetime.now().isoformat(),))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def mark_completed(self, reminder_id: int):
        """Mark a reminder as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE reminders
            SET completed = 1
            WHERE id = ?
        """, (reminder_id,))
        
        conn.commit()
        conn.close()


def send_telegram_notification(title: str, description: str, reminder_time: str, db_path: str):
    """Send reminder notification via Telegram"""
    try:
        # Try multiple config paths
        config_paths = [
            os.path.join(os.path.dirname(db_path), 'config.json'),
            'config.json',
            os.path.join(os.path.dirname(__file__), 'config.json'),
            '/home/dallas/mo11y/config.json',
            os.path.expanduser('~/mo11y/config.json')
        ]
        
        config = None
        config_path = None
        for path in config_paths:
            if os.path.exists(path):
                config_path = path
                logger.info(f"Found config at: {config_path}")
                with open(path, 'r') as f:
                    config = json.load(f)
                break
        
        if not config:
            logger.warning("No config.json found - cannot send Telegram notification")
            logger.info(f"Searched paths: {config_paths}")
            return False
        
        # Try multiple ways to get Telegram credentials
        # Check nested telegram object first
        telegram_config = config.get('telegram', {})
        bot_token = (telegram_config.get('bot_token') or
                    config.get('telegram_bot_token') or 
                    config.get('TELEGRAM_BOT_TOKEN') or
                    os.getenv('TELEGRAM_BOT_TOKEN'))
        user_id = (telegram_config.get('user_id') or
                  config.get('telegram_user_id') or 
                  config.get('TELEGRAM_USER_ID') or
                  os.getenv('TELEGRAM_USER_ID'))
        
        if not bot_token:
            logger.warning("No Telegram bot token found in config or environment")
            logger.info("Looking for: telegram_bot_token, TELEGRAM_BOT_TOKEN, or TELEGRAM_BOT_TOKEN env var")
            return False
        
        if not user_id:
            logger.warning("No Telegram user ID found in config or environment")
            logger.info("Looking for: telegram_user_id, TELEGRAM_USER_ID, or TELEGRAM_USER_ID env var")
            return False
        
        logger.info(f"Sending Telegram notification to user_id: {user_id}")
        
        message = f"🔔 **Reminder: {title}**\n"
        if description:
            message += f"{description}\n"
        message += f"\nDue: {reminder_time}"
        
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': int(user_id),
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        logger.debug(f"Telegram API URL: {api_url}")
        logger.debug(f"Payload: {payload}")
        
        response = requests.post(api_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info(f"✅ Telegram notification sent successfully for: {title}")
                return True
            else:
                logger.error(f"❌ Telegram API returned error: {result.get('description', 'Unknown error')}")
                return False
        else:
            logger.error(f"❌ Failed to send Telegram notification: HTTP {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending Telegram notification: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def trigger_alarm_script(title: str, description: str):
    """Trigger alarm.py script if it exists"""
    script_paths = [
        os.path.join(os.getcwd(), 'alarm.py'),
        os.path.join(os.path.dirname(__file__), 'alarm.py'),
        '/usr/local/bin/alarm.py',
        os.path.expanduser('~/alarm.py')
    ]
    
    for script_path in script_paths:
        if os.path.exists(script_path) and os.access(script_path, os.X_OK):
            try:
                subprocess.Popen(
                    ['python3', script_path, title, description],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info(f"Triggered alarm.py for: {title}")
                return
            except Exception as e:
                logger.debug(f"Could not execute alarm.py: {e}")
                continue


def trigger_ping_script(title: str, description: str):
    """Trigger ping.py script if it exists"""
    script_paths = [
        os.path.join(os.getcwd(), 'ping.py'),
        os.path.join(os.path.dirname(__file__), 'ping.py'),
        '/usr/local/bin/ping.py',
        os.path.expanduser('~/ping.py')
    ]
    
    for script_path in script_paths:
        if os.path.exists(script_path) and os.access(script_path, os.X_OK):
            try:
                subprocess.Popen(
                    ['python3', script_path, title, description],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info(f"Triggered ping.py for: {title}")
                return
            except Exception as e:
                logger.debug(f"Could not execute ping.py: {e}")
                continue


def open_flashing_webpage(title: str, description: str):
    """Open a flashing webpage notification"""
    try:
        # Create a simple HTML page with flashing effect
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Reminder: {title}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-family: Arial, sans-serif;
            animation: flash 0.5s infinite;
        }}
        @keyframes flash {{
            0%, 100% {{ background-color: #ff0000; }}
            50% {{ background-color: #ffff00; }}
        }}
        .content {{
            text-align: center;
            color: white;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            padding: 20px;
        }}
        h1 {{
            font-size: 3em;
            margin-bottom: 20px;
        }}
        p {{
            font-size: 1.5em;
        }}
    </style>
</head>
<body>
    <div class="content">
        <h1>🔔 REMINDER</h1>
        <h2>{title}</h2>
        <p>{description or 'No description'}</p>
    </div>
</body>
</html>"""
        
        # Save HTML to temp file
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
        temp_file.write(html_content)
        temp_file.close()
        
        # Open in browser
        file_url = f"file://{temp_file.name}"
        webbrowser.open(file_url)
        logger.info(f"Opened flashing webpage for: {title}")
        
        # Clean up after 30 seconds (optional)
        def cleanup():
            time.sleep(30)
            try:
                os.unlink(temp_file.name)
            except:
                pass
        
        import threading
        threading.Thread(target=cleanup, daemon=True).start()
        
    except Exception as e:
        logger.error(f"Error opening flashing webpage: {e}")


def main():
    """Main service loop for reminder daemon"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Get database path from environment or use default
    db_path = os.getenv('MO11Y_DB_PATH', './SPOHNZ.db')
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(db_path)
    
    # Get check interval from environment (default 60 seconds)
    check_interval = int(os.getenv('REMINDER_CHECK_INTERVAL', '60'))
    
    logger.info(f"Starting Reminder Service")
    logger.info(f"Database: {db_path}")
    logger.info(f"Check interval: {check_interval} seconds")
    
    # Initialize service
    try:
        service = ReminderService(db_path)
        logger.info("Reminder Service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Reminder Service: {e}")
        sys.exit(1)
    
    # Service loop
    logger.info("Entering service loop...")
    loop_count = 0
    try:
        while True:
            loop_count += 1
            try:
                # Log polling status every 10 loops (or every loop if check_interval < 60)
                if loop_count % max(1, 600 // check_interval) == 0 or loop_count == 1:
                    logger.info(f"Polling check #{loop_count} - Checking for reminders...")
                
                # Check for pending reminders
                pending = service.get_pending_reminders()
                
                if pending:
                    logger.info(f"🔔 Found {len(pending)} pending reminder(s)")
                    for reminder in pending:
                        reminder_id = reminder.get('id')
                        title = reminder.get('title', 'Untitled')
                        description = reminder.get('description', '')
                        reminder_time = reminder.get('reminder_time', 'Unknown time')
                        
                        logger.info(f"📢 Processing reminder: {title} (ID: {reminder_id}) - Due: {reminder_time}")
                        
                        # Send Telegram notification
                        logger.info(f"  → Sending Telegram notification...")
                        try:
                            send_telegram_notification(title, description, reminder_time, db_path)
                            logger.info(f"  ✅ Telegram notification sent successfully")
                        except Exception as e:
                            logger.error(f"  ❌ Failed to send Telegram notification: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                        
                        # Trigger alarm.py if it exists
                        logger.info(f"  → Checking for alarm.py...")
                        try:
                            trigger_alarm_script(title, description)
                        except Exception as e:
                            logger.debug(f"  ⚠️ Could not trigger alarm script: {e}")
                        
                        # Trigger ping.py if it exists
                        logger.info(f"  → Checking for ping.py...")
                        try:
                            trigger_ping_script(title, description)
                        except Exception as e:
                            logger.debug(f"  ⚠️ Could not trigger ping script: {e}")
                        
                        # Open flashing webpage if configured
                        logger.info(f"  → Opening flashing webpage...")
                        try:
                            open_flashing_webpage(title, description)
                        except Exception as e:
                            logger.debug(f"  ⚠️ Could not open flashing webpage: {e}")
                        
                        # Mark reminder as completed after notification
                        logger.info(f"  → Marking reminder {reminder_id} as completed...")
                        service.mark_completed(reminder_id)
                        logger.info(f"  ✅ Reminder {reminder_id} processed and marked complete")
                else:
                    if loop_count == 1 or loop_count % max(1, 600 // check_interval) == 0:
                        logger.info(f"No pending reminders found (check #{loop_count})")
                    else:
                        logger.debug(f"No pending reminders (check #{loop_count})")
                
            except Exception as e:
                logger.error(f"❌ Error checking reminders: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            # Sleep until next check
            logger.debug(f"Sleeping for {check_interval} seconds until next check...")
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        logger.info("Reminder Service stopped by user")
    except Exception as e:
        logger.error(f"Reminder Service error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
