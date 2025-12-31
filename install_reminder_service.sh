#!/bin/bash
# Install and start the Mo11y Reminder Service

echo "Installing Mo11y Reminder Service..."
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run with sudo: sudo ./install_reminder_service.sh"
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_FILE="$SCRIPT_DIR/mo11y-reminder.service"

if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ Service file not found: $SERVICE_FILE"
    exit 1
fi

# Copy service file
echo "📋 Copying service file..."
cp "$SERVICE_FILE" /etc/systemd/system/
echo "✅ Service file copied"

# Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload
echo "✅ Daemon reloaded"

# Enable service (this makes it start on boot)
echo "🔧 Enabling service (will start on boot)..."
systemctl enable mo11y-reminder.service
echo "✅ Service enabled - will start automatically after reboot"

# Start service
echo "🚀 Starting service..."
systemctl start mo11y-reminder.service
echo "✅ Service started"

# Check status
echo ""
echo "📊 Service status:"
systemctl status mo11y-reminder.service --no-pager -l

echo ""
echo "✅ Installation complete!"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u mo11y-reminder.service -f"
echo ""
echo "To restart service:"
echo "  sudo systemctl restart mo11y-reminder.service"
echo ""
echo "To stop service:"
echo "  sudo systemctl stop mo11y-reminder.service"
