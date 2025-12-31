#!/bin/bash
# Setup Mo11y Telegram Bot Service
# Installs and enables the Telegram bot as a systemd service

set -e

echo "📱 Setting up Mo11y Telegram Bot Service"
echo "========================================="
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script needs sudo privileges to install systemd services"
    echo "   Run with: sudo ./setup_telegram_bot.sh"
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_FILE="$SCRIPT_DIR/mo11y-telegram-bot.service"
SYSTEMD_DIR="/etc/systemd/system"

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ Service file not found: $SERVICE_FILE"
    exit 1
fi

# Check if telegram_bot_service.py exists
if [ ! -f "$SCRIPT_DIR/telegram_bot_service.py" ]; then
    echo "❌ telegram_bot_service.py not found: $SCRIPT_DIR/telegram_bot_service.py"
    exit 1
fi

echo "📋 Service file: $SERVICE_FILE"
echo "📋 Script directory: $SCRIPT_DIR"
echo ""

# Copy service file to systemd directory
echo "📝 Installing service file..."
cp "$SERVICE_FILE" "$SYSTEMD_DIR/mo11y-telegram-bot.service"
chmod 644 "$SYSTEMD_DIR/mo11y-telegram-bot.service"

# Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Enable service to start on boot
echo "✅ Enabling service to start on boot..."
systemctl enable mo11y-telegram-bot.service

# Start the service
echo "🚀 Starting Telegram bot service..."
systemctl start mo11y-telegram-bot.service

# Wait a moment for service to start
sleep 2

# Check status
echo ""
echo "📊 Service Status:"
echo ""
systemctl status mo11y-telegram-bot.service --no-pager -l

echo ""
echo "✅ Telegram bot service installed and started!"
echo ""
echo "Useful commands:"
echo "  sudo systemctl start mo11y-telegram-bot.service    # Start service"
echo "  sudo systemctl stop mo11y-telegram-bot.service     # Stop service"
echo "  sudo systemctl restart mo11y-telegram-bot.service # Restart service"
echo "  sudo systemctl status mo11y-telegram-bot.service    # Check status"
echo "  journalctl -u mo11y-telegram-bot.service -f        # View logs (follow)"
echo "  journalctl -u mo11y-telegram-bot.service -n 50     # View last 50 log lines"
echo ""
echo "📱 To test: Send a message to your Telegram bot!"
