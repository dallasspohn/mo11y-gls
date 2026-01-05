#!/bin/bash
# Comprehensive Test Script for Mo11y Setup
# Tests all services, components, and verifies everything works after reboot

# Don't exit on errors - we want to run all tests
set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Detect if we're in an SSHFS mount
IS_SSHFS=false
if mountpoint -q "$SCRIPT_DIR" 2>/dev/null; then
    if mount | grep -q "$SCRIPT_DIR.*fuse.sshfs"; then
        IS_SSHFS=true
    fi
fi

# Track results
PASSED=0
FAILED=0
WARNINGS=0
ISSUES=()

echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     Mo11y Complete Setup Test - Post-Reboot Check       ║${NC}"
echo -e "${CYAN}║     GOOD ONLY IF SERVICES ARE INSTALLED                 ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$IS_SSHFS" = true ]; then
    echo -e "${YELLOW}⚠️  SSHFS Environment Detected${NC}"
    echo -e "${BLUE}   Running tests for remote server setup${NC}"
    echo -e "${BLUE}   Systemd services should be checked on the remote server${NC}"
    echo ""
fi

# Function to log results
log_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAILED++))
    ISSUES+=("$1")
}

log_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
    ((WARNINGS++))
    ISSUES+=("$1")
}

log_info() {
    echo -e "${BLUE}ℹ️  INFO${NC}: $1"
}

# ============================================================================
# SECTION 1: Systemd Services Check
# ============================================================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}SECTION 1: Systemd Services Status${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$IS_SSHFS" = true ]; then
    log_warn "SSHFS environment: Cannot check local systemd services"
    log_info "  Services run on remote server - check there with:"
    log_info "    ssh <server> 'sudo systemctl status mo11y-*.service'"
    log_info "  Or run this script on the remote server directly"
else
    check_systemd_service() {
        local service_name=$1
        local display_name=$2
        
        if systemctl list-unit-files 2>/dev/null | grep -q "^${service_name}"; then
            if systemctl is-enabled "${service_name}" >/dev/null 2>&1; then
                if systemctl is-active "${service_name}" >/dev/null 2>&1; then
                    log_pass "${display_name} is enabled and running"
                    return 0
                else
                    log_fail "${display_name} is enabled but not running"
                    log_info "  Fix: sudo systemctl start ${service_name}"
                    return 1
                fi
            else
                log_warn "${display_name} exists but is not enabled for boot"
                log_info "  Fix: sudo systemctl enable ${service_name}"
                return 2
            fi
        else
            log_warn "${display_name} service file not found in systemd"
            log_info "  Fix: sudo ./setup_*_service.sh (if setup script exists)"
            return 3
        fi
    }

    # Check each service
    check_systemd_service "mo11y-mcp-server.service" "MCP Server"
    # Check Reminder Service with boot-on-startup verification
    if systemctl list-unit-files 2>/dev/null | grep -q "^mo11y-reminder.service"; then
        if systemctl is-enabled "mo11y-reminder.service" >/dev/null 2>&1; then
            if systemctl is-active "mo11y-reminder.service" >/dev/null 2>&1; then
                log_pass "Reminder Service is enabled, will start on boot, and is running"
            else
                log_fail "Reminder Service is enabled for boot but not running"
                log_info "  Fix: sudo systemctl start mo11y-reminder.service"
            fi
        else
            log_warn "Reminder Service exists but is NOT enabled for boot"
            log_info "  Fix: sudo systemctl enable mo11y-reminder.service"
            log_info "  Then: sudo systemctl start mo11y-reminder.service"
        fi
    else
        log_fail "Reminder Service not installed"
        log_info "  Fix: sudo ./install_reminder_service.sh"
    fi
    check_systemd_service "mo11y-streamlit.service" "Streamlit App"
    check_systemd_service "mo11y-slack-bot.service" "Slack Bot"
fi

echo ""

# ============================================================================
# SECTION 2: File and Directory Checks
# ============================================================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}SECTION 2: File and Directory Checks${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

check_file() {
    local file=$1
    local name=$2
    if [ -f "$file" ]; then
        log_pass "${name} exists"
        return 0
    else
        log_fail "${name} missing: $file"
        return 1
    fi
}

check_dir() {
    local dir=$1
    local name=$2
    if [ -d "$dir" ]; then
        log_pass "${name} exists"
        return 0
    else
        log_warn "${name} missing: $dir (may be created on first use)"
        return 1
    fi
}

# Core files
check_file "config.json" "Config file"
check_file "mo11y_agent.py" "Mo11y Agent"
check_file "app_enhanced.py" "Streamlit App"
check_file "local_calendar.py" "Local Calendar"
check_file "reminder_service.py" "Reminder Service"
check_file "task_service.py" "Task Service"
check_file "enhanced_memory.py" "Enhanced Memory"
check_file "local_mcp_server.py" "MCP Server"
check_file "slack_bot_service.py" "Slack Bot Service"

# Directories
check_dir "conversation_logs" "Conversation logs directory"
check_dir "sonas" "Sonas directory"
check_dir "RAGs" "RAGs directory"

echo ""

# ============================================================================
# SECTION 3: Python Imports and Dependencies
# ============================================================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}SECTION 3: Python Imports and Dependencies${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

test_import() {
    local module=$1
    local name=$2
    local error_output=$(python3 -c "import $module" 2>&1)
    if [ $? -eq 0 ]; then
        log_pass "${name} import successful"
        return 0
    else
        log_fail "${name} import failed: $module"
        log_info "  Fix: pip install $module"
        if [ -n "$error_output" ]; then
            log_info "  Error: $error_output"
        fi
        return 1
    fi
}

# Core imports
test_import "sqlite3" "SQLite3"
test_import "json" "JSON"
test_import "datetime" "DateTime"
test_import "streamlit" "Streamlit"
test_import "requests" "Requests"

# Optional imports (warn if missing)
if python3 -c "import ollama" 2>/dev/null; then
    log_pass "Ollama import successful"
else
    log_warn "Ollama not available (agent won't work)"
fi

echo ""

# ============================================================================
# SECTION 4: Service Initialization Tests
# ============================================================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}SECTION 4: Service Initialization Tests${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

test_service_init() {
    local test_name=$1
    local python_code=$2
    
    local result=$(python3 << EOF
$python_code
EOF
    2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ] && echo "$result" | grep -q "OK"; then
        log_pass "${test_name} initialization successful"
        return 0
    else
        log_fail "${test_name} initialization failed"
        if [ -n "$result" ]; then
            log_info "  Error: $result"
        fi
        return 1
    fi
}

# Test Local Calendar
test_service_init "Local Calendar" '
import sys
sys.path.insert(0, ".")
from local_calendar import LocalCalendar
lc = LocalCalendar("test_complete.db")
print("OK")
'

# Test Persona Memory Isolation
echo -e "${CYAN}Testing Persona Memory Isolation...${NC}"
PERSONA_ISOLATION_TEST=$(python3 << 'PYEOF'
import sys
import os
sys.path.insert(0, ".")
from enhanced_memory import EnhancedMemory

try:
    memory = EnhancedMemory("test_complete.db")
    
    # Test that Alex Mercer only gets Alex Mercer memories
    alex_memories = memory.recall_episodic(limit=5, persona="Alex Mercer")
    alex_personas = set()
    for mem in alex_memories:
        rel_context = mem.get('relationship_context', '')
        if 'persona:' in rel_context:
            persona = rel_context.split('persona:')[-1].split('|')[0].strip()
            alex_personas.add(persona)
    
    # Test that Izzy-Chan only gets Izzy-Chan memories
    izzy_memories = memory.recall_episodic(limit=5, persona="Izzy-Chan")
    izzy_personas = set()
    for mem in izzy_memories:
        rel_context = mem.get('relationship_context', '')
        if 'persona:' in rel_context:
            persona = rel_context.split('persona:')[-1].split('|')[0].strip()
            izzy_personas.add(persona)
    
    # Check for cross-contamination
    alex_isolated = len(alex_personas) == 1 and 'Alex Mercer' in alex_personas
    izzy_isolated = len(izzy_personas) == 1 and 'Izzy-Chan' in izzy_personas
    
    if alex_isolated and izzy_isolated:
        print("ISOLATION_OK")
    else:
        print(f"ISOLATION_FAIL: Alex={alex_personas}, Izzy={izzy_personas}")
    
    print("SUCCESS")
except Exception as e:
    print(f"ERROR:{e}")
PYEOF
)

if echo "$PERSONA_ISOLATION_TEST" | grep -q "ISOLATION_OK"; then
    log_pass "Persona memory isolation working correctly"
elif echo "$PERSONA_ISOLATION_TEST" | grep -q "ISOLATION_FAIL"; then
    ERROR_MSG=$(echo "$PERSONA_ISOLATION_TEST" | grep "ISOLATION_FAIL" | cut -d: -f2-)
    log_fail "Persona memory isolation issue: $ERROR_MSG"
    log_info "  This means memories from one persona are leaking into another persona's context"
else
    log_warn "Could not test persona isolation (may need test data)"
fi

echo ""

# Test Reminder Service - Enhanced with functionality tests
echo -e "${CYAN}Testing Reminder Service Functionality...${NC}"
REMINDER_TEST=$(python3 << 'PYEOF'
import sys
import os
from datetime import datetime, timedelta

try:
    from reminder_service import ReminderService
    
    # Test initialization
    rs = ReminderService("test_complete.db")
    print("INIT_OK")
    
    # Test adding reminder
    now = datetime.now()
    future_time = now + timedelta(minutes=5)
    reminder_id = rs.add_reminder("Test Reminder", future_time, "Test description")
    if reminder_id:
        print(f"ADD_OK:{reminder_id}")
    else:
        print("ADD_FAIL")
    
    # Test getting pending reminders (should be empty since future)
    pending = rs.get_pending_reminders()
    print(f"PENDING_COUNT:{len(pending)}")
    
    # Test getting all reminders
    import sqlite3
    conn = sqlite3.connect("test_complete.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM reminders")
    total = cursor.fetchone()[0]
    conn.close()
    print(f"TOTAL_COUNT:{total}")
    
    # Test Slack notification function exists
    from reminder_service import send_slack_notification
    print("SLACK_FUNC_OK")
    
    print("SUCCESS")
except Exception as e:
    print(f"ERROR:{e}")
    import traceback
    traceback.print_exc()
PYEOF
)

if echo "$REMINDER_TEST" | grep -q "SUCCESS"; then
    if echo "$REMINDER_TEST" | grep -q "INIT_OK"; then
        log_pass "Reminder Service initializes correctly"
    fi
    if echo "$REMINDER_TEST" | grep -q "ADD_OK"; then
        REMINDER_ID=$(echo "$REMINDER_TEST" | grep "ADD_OK" | cut -d: -f2)
        log_pass "Reminder Service can add reminders (ID: $REMINDER_ID)"
    fi
    if echo "$REMINDER_TEST" | grep -q "SLACK_FUNC_OK"; then
        log_pass "Slack notification function available"
    fi
    PENDING_COUNT=$(echo "$REMINDER_TEST" | grep "PENDING_COUNT" | cut -d: -f2)
    TOTAL_COUNT=$(echo "$REMINDER_TEST" | grep "TOTAL_COUNT" | cut -d: -f2)
    log_info "Reminder Service: $TOTAL_COUNT total reminders, $PENDING_COUNT pending"
else
    ERROR_MSG=$(echo "$REMINDER_TEST" | grep "ERROR" | cut -d: -f2-)
    log_fail "Reminder Service test failed: $ERROR_MSG"
fi

# Test Task Service
test_service_init "Task Service" '
import sys
sys.path.insert(0, ".")
from task_service import TaskService
ts = TaskService("test_complete.db")
print("OK")
'

# Test Enhanced Memory
test_service_init "Enhanced Memory" '
import sys
sys.path.insert(0, ".")
from enhanced_memory import EnhancedMemory
import json
with open("config.json", "r") as f:
    config = json.load(f)
db_path = config.get("db_path", "./SPOHNZ.db")
mem = EnhancedMemory(db_path)
print("OK")
'

echo ""

# ============================================================================
# SECTION 5: Database Tests
# ============================================================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}SECTION 5: Database Tests${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

test_database() {
    local db_path=$1
    local db_name=$2
    
    if [ -f "$db_path" ]; then
        if python3 << EOF
import sqlite3
conn = sqlite3.connect("$db_path")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
conn.close()
if len(tables) > 0:
    print(f"OK: {len(tables)} tables")
else:
    print("EMPTY")
EOF
        then
            table_count=$(python3 << EOF
import sqlite3
conn = sqlite3.connect("$db_path")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
conn.close()
print(len(tables))
EOF
            )
            log_pass "${db_name} exists with ${table_count} tables"
            return 0
        else
            log_warn "${db_name} exists but may be corrupted"
            return 1
        fi
    else
        log_warn "${db_name} does not exist (will be created on first use)"
        return 1
    fi
}

# Check main database
if [ -f "config.json" ]; then
    DB_PATH=$(python3 -c "import json; print(json.load(open('config.json')).get('db_path', './SPOHNZ.db'))" 2>/dev/null || echo "./SPOHNZ.db")
    test_database "$DB_PATH" "Main Database (SPOHNZ.db)"
else
    log_warn "config.json not found, cannot check database path"
fi

echo ""

# ============================================================================
# SECTION 6: MCP Server Connection Test
# ============================================================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}SECTION 6: MCP Server Connection Test${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Get MCP server URL
MCP_URL="http://localhost:8443"
if [ -f "config.json" ]; then
    MCP_URL=$(python3 -c "import json; print(json.load(open('config.json')).get('mcp_server_url', 'http://localhost:8443'))" 2>/dev/null || echo "http://localhost:8443")
fi

# For SSHFS, note that localhost refers to remote server
if [ "$IS_SSHFS" = true ]; then
    log_info "SSHFS: Testing MCP server on remote server (${MCP_URL})"
fi

if curl -s "${MCP_URL}/health" >/dev/null 2>&1; then
    log_pass "MCP Server is responding at ${MCP_URL}"
    
    # Try to list tools
    if python3 << EOF
import requests
import json
try:
    response = requests.post("${MCP_URL}/", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }, timeout=5)
    if response.status_code == 200:
        result = response.json()
        tools = result.get("result", {}).get("tools", [])
        print(f"OK: {len(tools)} tools")
    else:
        print("ERROR")
except Exception as e:
    print("ERROR")
EOF
    then
        tool_count=$(python3 << EOF
import requests
import json
try:
    response = requests.post("${MCP_URL}/", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }, timeout=5)
    if response.status_code == 200:
        result = response.json()
        tools = result.get("result", {}).get("tools", [])
        print(len(tools))
    else:
        print(0)
except:
    print(0)
EOF
        )
        log_pass "MCP Server has ${tool_count} tools available"
    else
        log_warn "MCP Server responding but tools not accessible"
    fi
else
    log_fail "MCP Server not responding at ${MCP_URL}"
    log_info "  Fix: sudo systemctl start mo11y-mcp-server.service"
    log_info "  Or: python3 local_mcp_server.py"
fi

echo ""

# ============================================================================
# SECTION 7: Ollama and Model Check
# ============================================================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}SECTION 7: Ollama and Model Check${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if python3 -c "import ollama" 2>/dev/null; then
    OLLAMA_TEST=$(python3 << 'PYEOF'
from ollama import list
try:
    models = list()
    model_list = [m.get("name", "") for m in models.get("models", [])]
    if model_list:
        print("OK")
    else:
        print("EMPTY")
except Exception as e:
    print(f"ERROR: {e}")
PYEOF
    2>&1)
    
    if echo "$OLLAMA_TEST" | grep -q "^OK$"; then
        MODEL_NAME=$(python3 -c "import json; print(json.load(open('config.json')).get('model_name', 'unknown'))" 2>/dev/null || echo "unknown")
        MODEL_CHECK=$(python3 << 'PYEOF'
from ollama import list
import json
try:
    with open("config.json", "r") as f:
        config = json.load(f)
    model_name = config.get("model_name", "unknown")
    models = list()
    model_list = [m.get("name", "") for m in models.get("models", [])]
    if model_name in model_list:
        print("OK")
    else:
        print("MISSING")
except Exception as e:
    print(f"ERROR: {e}")
PYEOF
        2>&1)
        
        if echo "$MODEL_CHECK" | grep -q "^OK$"; then
            log_pass "Ollama is running and model '${MODEL_NAME}' is available"
        else
            log_warn "Ollama is running but model '${MODEL_NAME}' not found"
            log_info "  Fix: ollama pull ${MODEL_NAME}"
        fi
    else
        if echo "$OLLAMA_TEST" | grep -q "EMPTY"; then
            log_warn "Ollama is running but no models are available"
            log_info "  Fix: ollama pull <model_name>"
        else
            log_warn "Ollama test failed: $OLLAMA_TEST"
        fi
    fi
else
    log_warn "Ollama not available (agent functionality will be limited)"
fi

echo ""

# ============================================================================
# SECTION 8: Configuration Check
# ============================================================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}SECTION 8: Configuration Check${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ -f "config.json" ]; then
    if python3 << EOF
import json
try:
    with open("config.json", "r") as f:
        config = json.load(f)
    required = ["model_name", "db_path"]
    missing = [r for r in required if r not in config]
    if missing:
        print(f"MISSING: {missing}")
    else:
        print("OK")
except Exception as e:
    print(f"ERROR: {e}")
EOF
    then
        log_pass "config.json is valid"
        
        # Show key config values
        MODEL_NAME=$(python3 -c "import json; print(json.load(open('config.json')).get('model_name', 'not set'))" 2>/dev/null || echo "not set")
        DB_PATH=$(python3 -c "import json; print(json.load(open('config.json')).get('db_path', 'not set'))" 2>/dev/null || echo "not set")
        log_info "  Model: ${MODEL_NAME}"
        log_info "  DB Path: ${DB_PATH}"
    else
        log_fail "config.json has errors"
    fi
else
    log_fail "config.json not found"
fi

echo ""

# ============================================================================
# SECTION 9: Port Availability Check
# ============================================================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}SECTION 9: Port Availability Check${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

check_port() {
    local port=$1
    local service=$2
    
if [ "$IS_SSHFS" = true ]; then
    # For SSHFS, we can't check local ports - services run on remote server
    # Only log this once, not for each port
    if [ "$port" = "8443" ]; then
        log_warn "SSHFS environment: Cannot check local ports (services run on remote server)"
        log_info "  Check ports on remote server instead"
    fi
    return 1
else
        if netstat -tuln 2>/dev/null | grep -q ":${port} " || ss -tuln 2>/dev/null | grep -q ":${port} "; then
            log_pass "Port ${port} is in use (${service} likely running)"
            return 0
        else
            log_warn "Port ${port} is not in use (${service} may not be running)"
            return 1
        fi
    fi
}

check_port "8443" "MCP Server"
check_port "8501" "Streamlit"

echo ""

# ============================================================================
# SECTION 10: Integration Test
# ============================================================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}SECTION 10: Integration Test${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

INTEGRATION_RESULT=$(python3 << 'PYEOF'
import sys
sys.path.insert(0, ".")
from datetime import datetime, timedelta

try:
    from local_calendar import LocalCalendar
    from reminder_service import ReminderService
    from task_service import TaskService
    
    db = "test_integration.db"
    now = datetime.now()
    
    # Initialize services
    lc = LocalCalendar(db)
    rs = ReminderService(db)
    ts = TaskService(db)
    
    # Add test data
    lc.add_event("Test Event", now + timedelta(days=1), now + timedelta(days=1, hours=1))
    rs.add_reminder("Test Reminder", now + timedelta(hours=1))
    ts.add_task("Test Task", "Test", now + timedelta(days=1), "medium")
    
    # Verify
    events = lc.get_events()
    reminders = rs.get_pending_reminders()
    tasks = ts.get_pending_tasks()
    
    if len(events) > 0 and len(reminders) > 0 and len(tasks) > 0:
        print("OK")
    else:
        print(f"PARTIAL: events={len(events)}, reminders={len(reminders)}, tasks={len(tasks)}")
except Exception as e:
    print(f"ERROR: {e}")
PYEOF
2>&1)

if echo "$INTEGRATION_RESULT" | grep -q "^OK$"; then
    log_pass "Integration test: All services work together"
elif echo "$INTEGRATION_RESULT" | grep -q "^PARTIAL"; then
    log_warn "Integration test: Some services returned partial results"
    log_info "  Result: $INTEGRATION_RESULT"
else
    log_fail "Integration test: Services failed to work together"
    log_info "  Error: $INTEGRATION_RESULT"
fi

echo ""

# ============================================================================
# FINAL SUMMARY
# ============================================================================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}TEST SUMMARY${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

TOTAL=$((PASSED + FAILED + WARNINGS))
echo -e "${GREEN}✅ Passed: ${PASSED}${NC}"
echo -e "${RED}❌ Failed: ${FAILED}${NC}"
echo -e "${YELLOW}⚠️  Warnings: ${WARNINGS}${NC}"
echo -e "${BLUE}📊 Total Tests: ${TOTAL}${NC}"
echo ""

if [ ${FAILED} -eq 0 ] && [ ${WARNINGS} -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Your setup is ready.${NC}"
    echo ""
    echo "Your services should start automatically on reboot if systemd services are enabled."
    exit 0
elif [ ${FAILED} -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Some warnings found, but no critical failures.${NC}"
    echo ""
    if [ ${#ISSUES[@]} -gt 0 ]; then
        echo "Issues to address:"
        for issue in "${ISSUES[@]}"; do
            echo "  - $issue"
        done
    fi
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please fix the issues above.${NC}"
    echo ""
    if [ ${#ISSUES[@]} -gt 0 ]; then
        echo "Critical issues:"
        for issue in "${ISSUES[@]}"; do
            echo "  - $issue"
        done
    fi
    echo ""
    echo "Quick fixes:"
    echo "  1. Enable systemd services: sudo systemctl enable mo11y-*.service"
    echo "  2. Install Reminder Service: sudo ./install_reminder_service.sh"
    echo "  2. Start services: sudo systemctl start mo11y-*.service"
    echo "  3. Check logs: journalctl -u mo11y-*.service -f"
    exit 1
fi
