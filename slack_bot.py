#!/usr/bin/env python3
"""
Slack Bot for Mo11y - Connect Alex (or any persona) to Slack
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


class SlackBot:
    """Slack bot that connects to Mo11y agent"""
    
    def __init__(self, bot_token: str, channel_id: str, agent, persona_name: str = "Alex Mercer"):
        """
        Initialize Slack bot
        
        Args:
            bot_token: Slack bot token (starts with xoxb-)
            channel_id: Slack channel ID or user ID (DM)
            agent: Mo11yAgent instance
            persona_name: Name of persona to use
        """
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.agent = agent
        self.persona_name = persona_name
        self.api_url = "https://slack.com/api"
        self.last_timestamp = None
        
    def get_me(self) -> Optional[Dict]:
        """Get bot information"""
        try:
            response = requests.post(
                f"{self.api_url}/auth.test",
                headers={"Authorization": f"Bearer {self.bot_token}"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data
            return None
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return None
    
    def send_message(self, text: str, thread_ts: Optional[str] = None) -> bool:
        """
        Send a message to the channel/user
        
        Args:
            text: Message text
            thread_ts: Optional thread timestamp (for replies)
        """
        try:
            payload = {
                'channel': self.channel_id,
                'text': text
            }
            if thread_ts:
                payload['thread_ts'] = thread_ts
            
            response = requests.post(
                f"{self.api_url}/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json"
                },
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
    
    def get_messages(self, limit: int = 10) -> list:
        """
        Get recent messages from the channel
        
        Args:
            limit: Maximum number of messages to retrieve
        """
        try:
            params = {
                'channel': self.channel_id,
                'limit': limit
            }
            if self.last_timestamp:
                params['oldest'] = self.last_timestamp
            
            response = requests.get(
                f"{self.api_url}/conversations.history",
                headers={"Authorization": f"Bearer {self.bot_token}"},
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    messages = data.get('messages', [])
                    if messages:
                        # Update last timestamp to the oldest message
                        self.last_timestamp = float(messages[-1].get('ts', 0))
                    return messages
            return []
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def process_message(self, message: Dict) -> Optional[str]:
        """
        Process an incoming message and return response
        
        Args:
            message: Slack message object
        """
        text = message.get('text', '').strip()
        if not text:
            return None
        
        # Ignore bot messages (including our own)
        if message.get('bot_id') or message.get('subtype') == 'bot_message':
            return None
        
        # Ignore messages from other channels/users
        channel = message.get('channel')
        if channel != self.channel_id:
            logger.info(f"Ignoring message from channel {channel} (expected {self.channel_id})")
            return None
        
        # Process with agent
        try:
            result = self.agent.chat(text, thread_id=f"slack_{self.channel_id}")
            response = result.get('response', '')
            
            # Filter out thinking tokens if needed
            if hasattr(self.agent, 'suppress_thinking') and self.agent.suppress_thinking:
                if hasattr(self.agent, '_filter_thinking_tokens'):
                    response = self.agent._filter_thinking_tokens(response)
            
            return response
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def run(self, poll_interval: int = 2):
        """
        Run the bot (polling mode)
        
        Args:
            poll_interval: Seconds between polls
        """
        logger.info(f"Starting Slack bot for {self.persona_name}...")
        
        # Verify bot token
        bot_info = self.get_me()
        if not bot_info:
            logger.error("Failed to verify bot token. Check your SLACK_BOT_TOKEN.")
            return
        
        bot_user_id = bot_info.get('user_id', 'unknown')
        bot_username = bot_info.get('user', 'unknown')
        logger.info(f"✅ Bot verified: {bot_username} ({bot_user_id})")
        
        # Send startup message
        self.send_message(
            f"👋 Hello! I'm {self.persona_name}, your AI companion.\n\n"
            f"I'm now connected via Slack. Send me a message to start chatting!"
        )
        
        logger.info(f"Bot is running. Listening for messages in channel {self.channel_id}...")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                messages = self.get_messages(limit=10)
                
                for message in reversed(messages):  # Process oldest first
                    # Only process text messages that are new
                    if 'text' in message and message.get('type') == 'message':
                        user_text = message.get('text', '')
                        logger.info(f"Received: {user_text[:50]}...")
                        
                        # Process and respond
                        response = self.process_message(message)
                        if response:
                            # Slack has a 4000 character limit per message
                            if len(response) > 3800:
                                # Split long messages
                                chunks = [response[i:i+3800] for i in range(0, len(response), 3800)]
                                thread_ts = message.get('ts')
                                for chunk in chunks:
                                    self.send_message(chunk, thread_ts=thread_ts)
                                    time.sleep(0.5)  # Small delay between chunks
                            else:
                                thread_ts = message.get('ts')
                                self.send_message(response, thread_ts=thread_ts)
                            
                            logger.info(f"Sent response ({len(response)} chars)")
                
                time.sleep(poll_interval)
                
        except KeyboardInterrupt:
            logger.info("\nShutting down bot...")
            self.send_message("👋 Goodbye! I'm going offline.")
        except Exception as e:
            logger.error(f"Error in bot loop: {e}")
            import traceback
            traceback.print_exc()


def create_slack_bot_from_config(agent, config_path: str = "config.json") -> Optional[SlackBot]:
    """
    Create Slack bot from config file
    
    Args:
        agent: Mo11yAgent instance
        config_path: Path to config.json
    """
    # Check environment variables first
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    channel_id = os.getenv('SLACK_CHANNEL_ID') or os.getenv('SLACK_USER_ID')
    
    # Fall back to config file
    if not bot_token or not channel_id:
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    slack_config = config.get('slack', {})
                    bot_token = bot_token or slack_config.get('bot_token')
                    channel_id = channel_id or slack_config.get('channel_id') or slack_config.get('user_id')
            except Exception as e:
                logger.error(f"Error reading config: {e}")
    
    if not bot_token:
        logger.error("SLACK_BOT_TOKEN not found in environment or config")
        logger.info("Note: Telegram is also supported as an optional alternative (see config.json)")
        return None
    
    if not channel_id:
        logger.error("SLACK_CHANNEL_ID or SLACK_USER_ID not found in environment or config")
        logger.info("Note: Telegram is also supported as an optional alternative (see config.json)")
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
    
    return SlackBot(bot_token, channel_id, agent, persona_name)


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
        bot = create_slack_bot_from_config(agent)
        if bot:
            bot.run()
        else:
            logger.error("Failed to create Slack bot. Check your configuration.")
            logger.info("Note: Telegram is also supported as an optional alternative (see config.json)")
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
