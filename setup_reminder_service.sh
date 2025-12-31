#!/bin/bash
# Setup Mo11y Reminder Service
# Installs and enables the reminder service as a systemd service

set -e

echo "📅 Setting up Mo11y Reminder Service"
echo "======================================"
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script needs sudo privileges to install systemd services"
    echo "   Run with: sudo ./setup_reminder_service.sh"
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_FILE="$SCRIPT_DIR/mo11y-reminder.service"
SYSTEMD_DIR="/etc/systemd/system"

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ Service file not found: $SERVICE_FILE"
    exit 1
fi

# Check if reminder_service.py exists
if [ ! -f "$SCRIPT_DIR/reminder_service.py" ]; then
    echo "❌ reminder_service.py not found: $SCRIPT_DIR/reminder_service.py"
    exit 1
fi

echo "📋 Service file: $SERVICE_FILE"
echo "📋 Script directory: $SCRIPT_DIR"
echo ""

# Copy service file to systemd directory
echo "📝 Installing service file..."
cp "$SERVICE_FILE" "$SYSTEMD_DIR/mo11y-reminder.service"
chmod 644 "$SYSTEMD_DIR/mo11y-reminder.service"

# Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Enable service to start on boot
echo "✅ Enabling service to start on boot..."
systemctl enable mo11y-reminder.service

# Start the service
echo "🚀 Starting reminder service..."
systemctl start mo11y-reminder.service

# Wait a moment for service to start
sleep 2

# Check status
echo ""
echo "📊 Service Status:"
echo ""
systemctl status mo11y-reminder.service --no-pager -l

echo ""
echo "✅ Reminder service installed and started!"
echo ""
echo "Useful commands:"
echo "  sudo systemctl start mo11y-reminder.service    # Start service"
echo "  sudo systemctl stop mo11y-reminder.service     # Stop service"
echo "  sudo systemctl restart mo11y-reminder.service  # Restart service"
echo "  sudo systemctl status mo11y-reminder.service   # Check status"
echo "  journalctl -u mo11y-reminder.service -f        # View logs (follow)"
echo "  journalctl -u mo11y-reminder.service -n 50     # View last 50 log lines"
echo ""
