#!/bin/bash
# Follow Mo11y service logs in real-time after reboot

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}📋 Checking Mo11y services...${NC}"
echo ""

# List of possible services
SERVICES=(
    "mo11y-mcp-server.service"
    "mo11y-reminder.service"
    "mo11y-streamlit.service"
    "mo11y-telegram-bot.service"
)

# Check which services exist and are active
ACTIVE_SERVICES=()
for service in "${SERVICES[@]}"; do
    if systemctl list-units --type=service --all | grep -q "$service"; then
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            ACTIVE_SERVICES+=("$service")
            echo -e "  ${GREEN}✅${NC} $service (active)"
        else
            echo -e "  ${YELLOW}⚠️${NC}  $service (exists but not active)"
        fi
    fi
done

echo ""

if [ ${#ACTIVE_SERVICES[@]} -eq 0 ]; then
    echo -e "${YELLOW}No active Mo11y services found.${NC}"
    echo ""
    echo "To check status of all services:"
    echo "  ./status_all_services.sh"
    echo ""
    echo "To start services:"
    echo "  ./start_all_services.sh"
    echo "  # or"
    echo "  sudo systemctl start mo11y-*.service"
    exit 1
fi

if [ ${#ACTIVE_SERVICES[@]} -eq 1 ]; then
    # Single service - follow it directly
    echo -e "${BLUE}Following logs for: ${ACTIVE_SERVICES[0]}${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    sudo journalctl -u "${ACTIVE_SERVICES[0]}" -f
else
    # Multiple services - use journalctl with multiple -u flags
    echo -e "${BLUE}Following logs for ${#ACTIVE_SERVICES[@]} services:${NC}"
    for service in "${ACTIVE_SERVICES[@]}"; do
        echo "  - $service"
    done
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    
    # Build journalctl command with multiple -u flags
    JCMD="sudo journalctl"
    for service in "${ACTIVE_SERVICES[@]}"; do
        JCMD="$JCMD -u $service"
    done
    JCMD="$JCMD -f"
    
    eval "$JCMD"
fi
