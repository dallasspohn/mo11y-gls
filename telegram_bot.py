#!/usr/bin/env python3
"""
Telegram Bot for Mo11y - Connect Alex (or any persona) to Telegram
"""

import json
import os
import requests
import time
from typing import Optional, Dict
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot that connects to Mo11y agent"""
    
    def __init__(self, bot_token: str, user_id: str, agent, persona_name: str = "Alex Mercer"):
        """
        Initialize Telegram bot
        
        Args:
            bot_token: Telegram bot token
            user_id: Telegram user ID (chat ID)
            agent: Mo11yAgent instance
            persona_name: Name of persona to use
        """
        self.bot_token = bot_token
        self.user_id = int(user_id)
        self.agent = agent
        self.persona_name = persona_name
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_update_id = 0
        
    def get_me(self) -> Optional[Dict]:
        """Get bot information"""
        try:
            response = requests.get(f"{self.api_url}/getMe", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get('result')
            return None
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return None
    
    def send_message(self, text: str, parse_mode: Optional[str] = None) -> bool:
        """
        Send a message to the user
        
        Args:
            text: Message text
            parse_mode: Optional parse mode (HTML, Markdown, etc.)
        """
        try:
            payload = {
                'chat_id': self.user_id,
                'text': text
            }
            if parse_mode:
                payload['parse_mode'] = parse_mode
            
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('ok', False)
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def get_updates(self, timeout: int = 0) -> list:
        """
        Get updates from Telegram
        
        Args:
            timeout: Long polling timeout (0 = short polling)
        """
        try:
            params = {
                'offset': self.last_update_id + 1,
                'timeout': timeout
            }
            
            response = requests.get(
                f"{self.api_url}/getUpdates",
                params=params,
                timeout=timeout + 5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    updates = data.get('result', [])
                    if updates:
                        self.last_update_id = max(u['update_id'] for u in updates)
                    return updates
            return []
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return []
    
    def process_message(self, message: Dict) -> Optional[str]:
        """
        Process an incoming message and return response
        
        Args:
            message: Telegram message object
        """
        text = message.get('text', '').strip()
        if not text:
            return None
        
        # Ignore messages from other users
        chat_id = message.get('chat', {}).get('id')
        if chat_id != self.user_id:
            logger.info(f"Ignoring message from chat_id {chat_id} (expected {self.user_id})")
            return None
        
        # Process with agent
        try:
            result = self.agent.chat(text, thread_id=f"telegram_{self.user_id}")
            response = result.get('response', '')
            
            # Filter out thinking tokens if needed
            if hasattr(self.agent, 'suppress_thinking') and self.agent.suppress_thinking:
                if hasattr(self.agent, '_filter_thinking_tokens'):
                    response = self.agent._filter_thinking_tokens(response)
            
            return response
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def run(self, poll_interval: int = 1):
        """
        Run the bot (polling mode)
        
        Args:
            poll_interval: Seconds between polls
        """
        logger.info(f"Starting Telegram bot for {self.persona_name}...")
        
        # Verify bot token
        bot_info = self.get_me()
        if not bot_info:
            logger.error("Failed to verify bot token. Check your TELEGRAM_BOT_TOKEN.")
            return
        
        bot_username = bot_info.get('username', 'unknown')
        logger.info(f"✅ Bot verified: @{bot_username}")
        
        # Send startup message
        self.send_message(
            f"👋 Hello! I'm {self.persona_name}, your AI companion.\n\n"
            f"I'm now connected via Telegram. Send me a message to start chatting!"
        )
        
        logger.info(f"Bot is running. Listening for messages from user {self.user_id}...")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                updates = self.get_updates(timeout=1)
                
                for update in updates:
                    if 'message' in update:
                        message = update['message']
                        
                        # Only process text messages
                        if 'text' in message:
                            user_text = message.get('text', '')
                            logger.info(f"Received: {user_text[:50]}...")
                            
                            # Process and respond
                            response = self.process_message(message)
                            if response:
                                # Telegram has a 4096 character limit per message
                                if len(response) > 4000:
                                    # Split long messages
                                    chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
                                    for chunk in chunks:
                                        self.send_message(chunk)
                                        time.sleep(0.5)  # Small delay between chunks
                                else:
                                    self.send_message(response)
                                
                                logger.info(f"Sent response ({len(response)} chars)")
                
                time.sleep(poll_interval)
                
        except KeyboardInterrupt:
            logger.info("\nShutting down bot...")
            self.send_message("👋 Goodbye! I'm going offline.")
        except Exception as e:
            logger.error(f"Error in bot loop: {e}")
            import traceback
            traceback.print_exc()


def create_telegram_bot_from_config(agent, config_path: str = "config.json") -> Optional[TelegramBot]:
    """
    Create Telegram bot from config file
    
    Args:
        agent: Mo11yAgent instance
        config_path: Path to config.json
    """
    # Check environment variables first
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    user_id = os.getenv('TELEGRAM_USER_ID')
    
    # Fall back to config file
    if not bot_token or not user_id:
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    telegram_config = config.get('telegram', {})
                    bot_token = bot_token or telegram_config.get('bot_token')
                    user_id = user_id or telegram_config.get('chat_id') or telegram_config.get('user_id')
            except Exception as e:
                logger.error(f"Error reading config: {e}")
    
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment or config")
        return None
    
    if not user_id:
        logger.error("TELEGRAM_USER_ID not found in environment or config")
        return None
    
    # Get persona name from agent
    persona_name = "Alex Mercer"
    if agent.sona_path:
        try:
            with open(agent.sona_path, 'r') as f:
                sona_data = json.load(f)
                persona_name = sona_data.get('name', persona_name)
        except:
            pass
    
    return TelegramBot(bot_token, user_id, agent, persona_name)


if __name__ == "__main__":
    import sys
    
    # Import agent
    try:
        from mo11y_agent import create_mo11y_agent
        import json
        
        # Load config
        config_path = "config.json"
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        # Get persona path (default to Alex Mercer)
        sona_path = None
        sonas_dir = config.get('sonas_dir', './sonas/')
        if not os.path.isabs(sonas_dir):
            sonas_dir = os.path.abspath(sonas_dir)
        
        # Look for Alex Mercer persona
        alex_path = os.path.join(sonas_dir, 'alex-mercer.json')
        if os.path.exists(alex_path):
            sona_path = alex_path
        else:
            # Try to find any persona
            if os.path.exists(sonas_dir):
                for file in os.listdir(sonas_dir):
                    if file.endswith('.json') and 'alex' in file.lower():
                        sona_path = os.path.join(sonas_dir, file)
                        break
        
        # Create agent
        db_path = config.get('db_path', 'SPOHNZ.db')
        model_name = config.get('model_name', 'deepseek-r1:latest')
        
        logger.info(f"Creating agent with persona: {sona_path}")
        agent = create_mo11y_agent(
            model_name=model_name,
            db_path=db_path,
            sona_path=sona_path,
            enable_mcp=True,
            enable_external_apis=True
        )
        
        # Create bot
        bot = create_telegram_bot_from_config(agent)
        if bot:
            bot.run()
        else:
            logger.error("Failed to create Telegram bot. Check your configuration.")
            sys.exit(1)
            
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
