#!/usr/bin/env python3
"""
Telegram Bot Service - Systemd service wrapper for Telegram bot
"""

import os
import sys
import json
import logging
from telegram_bot import create_telegram_bot_from_config
from mo11y_agent import create_mo11y_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for Telegram bot service"""
    try:
        # Load config
        config_path = os.getenv('MO11Y_CONFIG_PATH', 'config.json')
        if not os.path.exists(config_path):
            logger.error(f"Config file not found: {config_path}")
            sys.exit(1)
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Get paths
        sonas_dir = config.get('sonas_dir', './sonas/')
        if not os.path.isabs(sonas_dir):
            sonas_dir = os.path.abspath(sonas_dir)
        
        db_path = config.get('db_path', './SPOHNZ.db')
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)
        
        model_name = config.get('model_name', 'deepseek-r1:latest')
        
        # Find Alex Mercer persona
        sona_path = None
        alex_path = os.path.join(sonas_dir, 'alex-mercer.json')
        if os.path.exists(alex_path):
            sona_path = alex_path
            logger.info(f"Using Alex Mercer persona: {sona_path}")
        else:
            logger.warning(f"Alex Mercer persona not found at {alex_path}")
            logger.info("Bot will use default persona")
        
        # Create agent
        logger.info("Creating Mo11y agent...")
        agent = create_mo11y_agent(
            model_name=model_name,
            db_path=db_path,
            sona_path=sona_path,
            enable_mcp=True,
            enable_external_apis=True,
            enable_logging=True
        )
        
        logger.info("Agent created successfully")
        
        # Create Telegram bot
        logger.info("Creating Telegram bot...")
        bot = create_telegram_bot_from_config(agent, config_path)
        
        if not bot:
            logger.error("Failed to create Telegram bot")
            sys.exit(1)
        
        # Run bot
        logger.info("Starting Telegram bot...")
        bot.run(poll_interval=1)
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
