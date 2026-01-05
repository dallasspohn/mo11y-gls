#!/bin/bash
# Check Status of All Mo11y Services

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/.service_pids"
LOG_DIR="$SCRIPT_DIR/.service_logs"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 Mo11y Services Status${NC}"
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

# Function to get process info
get_process_info() {
    local pid=$1
    if is_running "$pid"; then
        # Get CPU and memory usage
        ps -p "$pid" -o pid,pcpu,pmem,etime,cmd --no-headers 2>/dev/null || echo ""
    fi
}

# Function to get last few lines of log
get_log_tail() {
    local log_file=$1
    local lines=${2:-5}
    if [ -f "$log_file" ]; then
        tail -n "$lines" "$log_file" 2>/dev/null | sed 's/^/    /'
    else
        echo "    (No log file)"
    fi
}

check_service() {
    local service_name=$1
    local display_name=$2
    local pid_file="$PID_DIR/${service_name}.pid"
    local log_file="$LOG_DIR/${service_name}.log"
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$display_name${NC}"
    echo ""
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if is_running "$pid"; then
            echo -e "  Status: ${GREEN}✅ Running${NC}"
            echo "  PID: $pid"
            
            local info=$(get_process_info "$pid")
            if [ -n "$info" ]; then
                echo "  CPU: $(echo "$info" | awk '{print $2}')%"
                echo "  Memory: $(echo "$info" | awk '{print $3}')%"
                echo "  Uptime: $(echo "$info" | awk '{print $4}')"
            fi
            
            echo ""
            echo "  Recent log output:"
            get_log_tail "$log_file" 3
        else
            echo -e "  Status: ${RED}❌ Not Running${NC}"
            echo "  PID file exists but process is dead"
            echo ""
            echo "  Last log output:"
            get_log_tail "$log_file" 5
        fi
    else
        echo -e "  Status: ${YELLOW}⚠️  Not Started${NC}"
        echo "  No PID file found"
    fi
    echo ""
}

check_service "mcp_server" "📡 MCP Server"
check_service "reminder_service" "⏰ Reminder Service"
check_service "slack_bot" "💬 Slack Bot"
check_service "streamlit" "🌐 Streamlit"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📝 Full logs available in: $LOG_DIR/"
echo ""
echo "To view logs in real-time:"
echo "  tail -f $LOG_DIR/mcp_server.log"
echo "  tail -f $LOG_DIR/reminder_service.log"
echo "  tail -f $LOG_DIR/slack_bot.log"
echo "  tail -f $LOG_DIR/streamlit.log"
