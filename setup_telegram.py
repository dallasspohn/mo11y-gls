#!/usr/bin/env python3
"""
Setup Telegram notifications for reminders
"""

import json
import os
import requests


def setup_telegram():
    """Interactive Telegram setup"""
    print("📱 Telegram Notification Setup")
    print("=" * 50)
    
    print("\n📝 Instructions:")
    print("1. Open Telegram and search for '@BotFather'")
    print("2. Send '/newbot' to BotFather")
    print("3. Follow instructions to create a bot")
    print("4. Copy the bot token (looks like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)")
    print("5. Send '/start' to your new bot")
    print("6. Get your chat ID by visiting: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates")
    print("   Look for 'chat':{'id':123456789} in the response")
    print("\n" + "=" * 50)
    
    bot_token = input("\nEnter your Telegram bot token: ").strip()
    if not bot_token:
        print("❌ Bot token is required")
        return False
    
    # Test the bot token
    print("\n⏳ Testing bot token...")
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                print(f"✅ Bot verified: @{bot_info['result'].get('username', 'unknown')}")
            else:
                print(f"❌ Invalid bot token: {bot_info.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ Failed to verify bot token: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing bot token: {e}")
        return False
    
    chat_id = input("\nEnter your Telegram chat ID (numeric): ").strip()
    if not chat_id:
        print("❌ Chat ID is required")
        return False
    
    try:
        chat_id_int = int(chat_id)
    except ValueError:
        print("❌ Chat ID must be a number")
        return False
    
    # Test sending a message
    print("\n⏳ Testing notification...")
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id_int,
            'text': '✅ Telegram notifications are now set up! You will receive reminders here.'
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Test message sent successfully!")
        else:
            print(f"⚠️ Could not send test message: {response.text}")
    except Exception as e:
        print(f"⚠️ Could not send test message: {e}")
    
    # Save to config.json
    config_path = "config.json"
    config = {}
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except:
            pass
    
    if 'telegram' not in config:
        config['telegram'] = {}
    
    config['telegram']['bot_token'] = bot_token
    config['telegram']['chat_id'] = chat_id
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\n✅ Telegram configuration saved to {config_path}")
        print("\n🎉 Setup complete! The reminder service will use Telegram for notifications.")
        return True
    except Exception as e:
        print(f"\n❌ Error saving config: {e}")
        return False


if __name__ == "__main__":
    setup_telegram()
