#!/bin/bash
# Stop All Mo11y Services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/.service_pids"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Stopping Mo11y Services...${NC}"
echo ""

# Function to check if a process is running
is_running() {
    local pid=$1
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Stop services in reverse order
SERVICES=("streamlit" "slack_bot" "reminder_service" "mcp_server")
STOPPED=0
FAILED=0

for service in "${SERVICES[@]}"; do
    pid_file="$PID_DIR/${service}.pid"
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        service_name=$(echo "$service" | tr '_' ' ')
        
        if is_running "$pid"; then
            echo -e "  Stopping ${service_name} (PID: $pid)..."
            if kill "$pid" 2>/dev/null; then
                # Wait up to 5 seconds for graceful shutdown
                for i in {1..5}; do
                    if ! is_running "$pid"; then
                        break
                    fi
                    sleep 1
                done
                
                # Force kill if still running
                if is_running "$pid"; then
                    echo -e "    ${YELLOW}Force killing...${NC}"
                    kill -9 "$pid" 2>/dev/null || true
                    sleep 1
                fi
                
                if ! is_running "$pid"; then
                    echo -e "    ${GREEN}✅ Stopped${NC}"
                    ((STOPPED++))
                else
                    echo -e "    ${RED}❌ Failed to stop${NC}"
                    ((FAILED++))
                fi
            else
                echo -e "    ${RED}❌ Failed to send stop signal${NC}"
                ((FAILED++))
            fi
        else
            echo -e "  ${YELLOW}⚠️${NC}  ${service_name}: Not running (stale PID file)"
        fi
        
        rm -f "$pid_file"
    else
        echo -e "  ${YELLOW}⚠️${NC}  ${service_name}: No PID file found"
    fi
done

echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All services stopped successfully!${NC}"
else
    echo -e "${YELLOW}⚠️  Stopped $STOPPED services, $FAILED failed${NC}"
fi
