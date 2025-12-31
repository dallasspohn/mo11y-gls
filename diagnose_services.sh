#!/bin/bash
# Diagnostic script for Mo11y services

echo "🔍 Mo11y Service Diagnostics"
echo "============================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_service() {
    local service=$1
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "Checking: $service"
    echo ""
    
    # Check if service exists
    if systemctl list-unit-files | grep -q "^${service}"; then
        echo -e "${GREEN}✅ Service file exists${NC}"
    else
        echo -e "${RED}❌ Service file not found${NC}"
        return
    fi
    
    # Check status
    echo ""
    echo "Status:"
    systemctl status "$service" --no-pager -l | head -15
    
    # Check recent logs
    echo ""
    echo "Recent logs (last 20 lines):"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    journalctl -u "$service" -n 20 --no-pager || echo "No logs found"
    
    echo ""
    echo ""
}

# Check both services
check_service "mo11y-reminder.service"
check_service "mo11y-telegram-bot.service"

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "💡 To manually test services:"
echo ""
echo "Reminder Service:"
echo "  sudo systemctl start mo11y-reminder.service"
echo "  sudo systemctl status mo11y-reminder.service"
echo ""
echo "Telegram Bot:"
echo "  sudo systemctl start mo11y-telegram-bot.service"
echo "  sudo systemctl status mo11y-telegram-bot.service"
echo ""
