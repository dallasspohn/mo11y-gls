#!/bin/bash
# Bounce Mo11y Services
# Stops and restarts both MCP server and Streamlit services in the correct order

echo "🔄 Bouncing Mo11y Services..."
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script needs sudo privileges to manage systemd services"
    echo "   Run with: sudo ./bounce_services.sh"
    exit 1
fi

# Stop services in reverse order (Streamlit first, then MCP server)
echo "🛑 Stopping services..."
systemctl stop mo11y-streamlit.service
sleep 2
systemctl stop mo11y-mcp-server.service
sleep 2

echo "✅ Services stopped"
echo ""

# Start services in correct order (MCP server first, then Streamlit)
echo "🚀 Starting services..."
systemctl start mo11y-mcp-server.service
sleep 3
systemctl start mo11y-streamlit.service
sleep 2

echo "✅ Services started"
echo ""

# Check status
echo "📊 Service Status:"
echo ""
systemctl status mo11y-mcp-server.service --no-pager -l
echo ""
systemctl status mo11y-streamlit.service --no-pager -l

echo ""
echo "✅ Bounce complete!"
echo ""
echo "To view logs:"
echo "  journalctl -u mo11y-mcp-server.service -f"
echo "  journalctl -u mo11y-streamlit.service -f"
