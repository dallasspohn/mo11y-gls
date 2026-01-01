#!/bin/bash
# Start All Mo11y Services (without systemd)
# Starts Telegram bot, MCP server, Reminder service, and Streamlit in background

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/.service_pids"
LOG_DIR="$SCRIPT_DIR/.service_logs"

# Create directories for PIDs and logs
mkdir -p "$PID_DIR" "$LOG_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Mo11y Services...${NC}"
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

# Function to stop existing services
stop_existing() {
    echo -e "${YELLOW}🛑 Stopping any existing services...${NC}"
    
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            service_name=$(basename "$pid_file" .pid)
            if is_running "$pid"; then
                echo "  Stopping $service_name (PID: $pid)..."
                kill "$pid" 2>/dev/null || true
                sleep 1
                # Force kill if still running
                if is_running "$pid"; then
                    kill -9 "$pid" 2>/dev/null || true
                fi
            fi
            rm -f "$pid_file"
        fi
    done
    echo ""
}

# Stop any existing services first
stop_existing

# Set up environment variables
export MO11Y_CONFIG_PATH="${MO11Y_CONFIG_PATH:-$SCRIPT_DIR/config.json}"
export REMINDER_CHECK_INTERVAL="${REMINDER_CHECK_INTERVAL:-60}"
export MO11Y_DB_PATH="${MO11Y_DB_PATH:-$SCRIPT_DIR/mo11y_companion.db}"

# Check for Telegram bot token
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    if [ -f "$MO11Y_CONFIG_PATH" ]; then
        # Try to extract from config.json
        TELEGRAM_BOT_TOKEN=$(python3 -c "import json; print(json.load(open('$MO11Y_CONFIG_PATH')).get('telegram', {}).get('bot_token', ''))" 2>/dev/null || echo "")
    fi
    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
        echo -e "${YELLOW}⚠️  TELEGRAM_BOT_TOKEN not set. Telegram bot may not start properly.${NC}"
    else
        export TELEGRAM_BOT_TOKEN
    fi
fi

if [ -z "$TELEGRAM_USER_ID" ]; then
    if [ -f "$MO11Y_CONFIG_PATH" ]; then
        TELEGRAM_USER_ID=$(python3 -c "import json; print(json.load(open('$MO11Y_CONFIG_PATH')).get('telegram', {}).get('user_id', ''))" 2>/dev/null || echo "")
    fi
    if [ -n "$TELEGRAM_USER_ID" ]; then
        export TELEGRAM_USER_ID
    fi
fi

# 1. Start MCP Server (must start first)
echo -e "${GREEN}📡 Starting MCP Server...${NC}"
# Use venv from current directory if it exists, otherwise try system Python
if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_CMD="$SCRIPT_DIR/.venv/bin/python"
elif [ -f "/home/dallas/venv/bin/python" ]; then
    PYTHON_CMD="/home/dallas/venv/bin/python"
else
    PYTHON_CMD="python3"
fi

if [ -f "$SCRIPT_DIR/local_mcp_server.py" ]; then
    cd "$SCRIPT_DIR"
    $PYTHON_CMD local_mcp_server.py > "$LOG_DIR/mcp_server.log" 2>&1 &
    MCP_PID=$!
    echo "$MCP_PID" > "$PID_DIR/mcp_server.pid"
    echo "  ✅ MCP Server started (PID: $MCP_PID)"
    sleep 3  # Give MCP server time to start
else
    echo -e "${YELLOW}⚠️  local_mcp_server.py not found, skipping MCP server...${NC}"
fi
cd "$SCRIPT_DIR"
echo ""

# 2. Start Reminder Service
echo -e "${GREEN}⏰ Starting Reminder Service...${NC}"
if [ -f "$SCRIPT_DIR/reminder_service.py" ]; then
    $PYTHON_CMD "$SCRIPT_DIR/reminder_service.py" > "$LOG_DIR/reminder_service.log" 2>&1 &
    REMINDER_PID=$!
    echo "$REMINDER_PID" > "$PID_DIR/reminder_service.pid"
    echo "  ✅ Reminder Service started (PID: $REMINDER_PID)"
    sleep 1
else
    echo -e "${RED}❌ reminder_service.py not found${NC}"
fi
echo ""

# 3. Start Telegram Bot
echo -e "${GREEN}💬 Starting Telegram Bot...${NC}"
if [ -f "$SCRIPT_DIR/telegram_bot_service.py" ]; then
    $PYTHON_CMD "$SCRIPT_DIR/telegram_bot_service.py" > "$LOG_DIR/telegram_bot.log" 2>&1 &
    TELEGRAM_PID=$!
    echo "$TELEGRAM_PID" > "$PID_DIR/telegram_bot.pid"
    echo "  ✅ Telegram Bot started (PID: $TELEGRAM_PID)"
    sleep 1
else
    echo -e "${RED}❌ telegram_bot_service.py not found${NC}"
fi
echo ""

# 4. Start Streamlit (depends on MCP server)
echo -e "${GREEN}🌐 Starting Streamlit...${NC}"
if [ -f "$SCRIPT_DIR/app_enhanced.py" ]; then
    # Use venv from current directory if it exists
    if [ -f "$SCRIPT_DIR/.venv/bin/streamlit" ]; then
        STREAMLIT_CMD="$SCRIPT_DIR/.venv/bin/streamlit"
    elif [ -f "/home/dallas/venv/bin/streamlit" ]; then
        STREAMLIT_CMD="/home/dallas/venv/bin/streamlit"
    else
        STREAMLIT_CMD="streamlit"
    fi
    $STREAMLIT_CMD run "$SCRIPT_DIR/app_enhanced.py" > "$LOG_DIR/streamlit.log" 2>&1 &
    STREAMLIT_PID=$!
    echo "$STREAMLIT_PID" > "$PID_DIR/streamlit.pid"
    echo "  ✅ Streamlit started (PID: $STREAMLIT_PID)"
    sleep 2
else
    echo -e "${RED}❌ app_enhanced.py not found${NC}"
fi
echo ""

# Wait a moment for all services to initialize
sleep 2

# Check status
echo -e "${GREEN}📊 Service Status:${NC}"
echo ""

check_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if is_running "$pid"; then
            echo -e "  ${GREEN}✅${NC} $service_name: Running (PID: $pid)"
            return 0
        else
            echo -e "  ${RED}❌${NC} $service_name: Not running (PID file exists but process dead)"
            return 1
        fi
    else
        echo -e "  ${YELLOW}⚠️${NC}  $service_name: Not started"
        return 1
    fi
}

check_service "mcp_server"
check_service "reminder_service"
check_service "telegram_bot"
check_service "streamlit"

echo ""
echo -e "${GREEN}✅ All services started!${NC}"
echo ""
echo "📝 Logs are available in: $LOG_DIR/"
echo "   - mcp_server.log"
echo "   - reminder_service.log"
echo "   - telegram_bot.log"
echo "   - streamlit.log"
echo ""
echo "🛑 To stop all services, run:"
echo "   ./stop_all_services.sh"
echo ""
echo "📋 To check status, run:"
echo "   ./status_all_services.sh"
echo ""
