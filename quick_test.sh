#!/bin/bash
# Quick test script for Mo11y features

echo "🧪 Mo11y Quick Test Suite"
echo "=========================="
echo ""

# Test 1: Imports
echo "1. Testing imports..."
python3 -c "from local_calendar import LocalCalendar; from reminder_service import ReminderService; from task_service import TaskService; print('✅ All imports successful')" || echo "❌ Import failed"

# Test 2: Services initialization
echo ""
echo "2. Testing service initialization..."
python3 << 'EOF'
from local_calendar import LocalCalendar
from reminder_service import ReminderService
from task_service import TaskService

lc = LocalCalendar('test_quick.db')
rs = ReminderService('test_quick.db')
ts = TaskService('test_quick.db')
print('✅ All services initialized')
EOF

# Test 3: Basic operations
echo ""
echo "3. Testing basic operations..."
python3 << 'EOF'
from local_calendar import LocalCalendar
from reminder_service import ReminderService
from task_service import TaskService
from datetime import datetime, timedelta

db = 'test_quick.db'
now = datetime.now()

lc = LocalCalendar(db)
rs = ReminderService(db)
ts = TaskService(db)

# Add test data
lc.add_event('Quick Test Event', now + timedelta(days=1), now + timedelta(days=1, hours=1))
rs.add_reminder('Quick Test Reminder', now + timedelta(hours=1))
ts.add_task('Quick Test Task', 'Test', now + timedelta(days=1), 'medium')

# Verify
events = lc.get_events()
reminders = rs.get_pending_reminders()
tasks = ts.get_pending_tasks()

print(f'✅ Calendar: {len(events)} events')
print(f'✅ Reminders: {len(reminders)} reminders')
print(f'✅ Tasks: {len(tasks)} tasks')
EOF

# Test 4: Database tables
echo ""
echo "4. Testing database tables..."
python3 << 'EOF'
import sqlite3
import json
import os

# Get database path from config or use default
db_path = 'SPOHNZ.db'
try:
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            config = json.load(f)
            db_path = config.get('db_path', 'SPOHNZ.db')
            # Handle relative paths
            if not os.path.isabs(db_path):
                db_path = os.path.abspath(db_path)
except:
    pass

# Initialize services to ensure tables are created
from local_calendar import LocalCalendar
from reminder_service import ReminderService
from task_service import TaskService

try:
    # Initialize services with the main database to create tables
    lc = LocalCalendar(db_path)
    rs = ReminderService(db_path)
    ts = TaskService(db_path)
    
    # Now check if tables exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    required = ['calendar_events', 'reminders', 'tasks']
    missing = [t for t in required if t not in tables]
    
    if missing:
        print(f'❌ Missing tables in {db_path}: {missing}')
        print(f'   Found tables: {tables}')
    else:
        print(f'✅ All required tables exist in {db_path}')
    conn.close()
except Exception as e:
    print(f'⚠️ Error checking database: {e}')
    import traceback
    traceback.print_exc()
EOF

# Test 5: Log directory
echo ""
echo "5. Testing log directory..."
if [ -d "conversation_logs" ]; then
    echo "✅ Log directory exists"
else
    echo "❌ Log directory missing"
fi

# Test 6: File existence
echo ""
echo "6. Testing file existence..."
files=("local_calendar.py" "reminder_service.py" "task_service.py" "mo11y_agent.py" "app_enhanced.py")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
    fi
done

echo ""
echo "=========================="
echo "✅ Quick test complete!"
