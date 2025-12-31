#!/usr/bin/env python3
"""
Alarm script - triggered by reminder service
Can be customized for audio alerts, system notifications, etc.
"""

import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main alarm function"""
    title = sys.argv[1] if len(sys.argv) > 1 else "Reminder"
    description = sys.argv[2] if len(sys.argv) > 2 else ""
    
    logger.info(f"ALARM TRIGGERED: {title}")
    if description:
        logger.info(f"Description: {description}")
    
    # Add your custom alarm logic here
    # Examples:
    # - Play sound file: os.system("aplay /path/to/alarm.wav")
    # - System notification: os.system("notify-send 'Reminder' '{title}'")
    # - Log to file
    # - Send to external service
    
    # Example: System notification (Linux)
    try:
        os.system(f"notify-send '🔔 Reminder' '{title}\\n{description}'")
    except:
        pass
    
    # Example: Log to file
    log_file = os.path.expanduser("~/alarm.log")
    try:
        with open(log_file, 'a') as f:
            from datetime import datetime
            f.write(f"{datetime.now().isoformat()} - {title}: {description}\n")
    except Exception as e:
        logger.error(f"Could not write to alarm log: {e}")


if __name__ == "__main__":
    main()
