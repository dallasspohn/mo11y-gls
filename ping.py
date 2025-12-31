#!/usr/bin/env python3
"""
Ping script - triggered by reminder service
Can be customized for network pings, API calls, etc.
"""

import sys
import os
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main ping function"""
    title = sys.argv[1] if len(sys.argv) > 1 else "Reminder"
    description = sys.argv[2] if len(sys.argv) > 2 else ""
    
    logger.info(f"PING TRIGGERED: {title}")
    if description:
        logger.info(f"Description: {description}")
    
    # Add your custom ping logic here
    # Examples:
    # - Ping a server: os.system("ping -c 1 example.com")
    # - Send HTTP request: requests.get("http://example.com/api/notify")
    # - Trigger webhook
    # - Send email
    
    # Example: Log to file
    log_file = os.path.expanduser("~/ping.log")
    try:
        with open(log_file, 'a') as f:
            from datetime import datetime
            f.write(f"{datetime.now().isoformat()} - {title}: {description}\n")
    except Exception as e:
        logger.error(f"Could not write to ping log: {e}")
    
    # Example: Send webhook (uncomment and configure)
    # webhook_url = os.getenv("REMINDER_WEBHOOK_URL")
    # if webhook_url:
    #     try:
    #         requests.post(webhook_url, json={
    #             "title": title,
    #             "description": description,
    #             "timestamp": datetime.now().isoformat()
    #         }, timeout=5)
    #     except Exception as e:
    #         logger.error(f"Webhook failed: {e}")


if __name__ == "__main__":
    main()
