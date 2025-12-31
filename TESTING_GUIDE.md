# Mo11y Testing Guide

**Last Updated**: December 29, 2025

Use this guide to test all features after any changes to ensure everything still works correctly.

---

## Quick Test Checklist

- [ ] Simple Question Handler (time/date)
- [ ] Local Calendar Service
- [ ] Reminder Service
- [ ] Task Service
- [ ] Agent Integration
- [ ] Conversation Timestamps
- [ ] Database Operations
- [ ] Conversation Logging

---

## 1. Simple Question Handler

### Test: Time Questions
**Test in Streamlit app:**
```
What time is it?
What's the time?
Current time?
Time now?
```

**Expected Results:**
- ✅ Response appears immediately (no model call)
- ✅ Shows current time in format: "It's currently 02:33 PM."
- ✅ Uses local computer time
- ✅ Response has timestamp displayed

### Test: Date Questions
**Test in Streamlit app:**
```
What date is it?
What's the date?
What day is it?
Current date?
```

**Expected Results:**
- ✅ Response appears immediately (no model call)
- ✅ Shows current date in format: "Today is Monday, December 29, 2025."
- ✅ Uses local computer time
- ✅ Response has timestamp displayed

---

## 2. Local Calendar Service

### Test: Import and Initialize
```bash
cd /home/dallas/mo11y
python3 -c "from local_calendar import LocalCalendar; lc = LocalCalendar('test_calendar.db'); print('✅ Local Calendar imported and initialized')"
```

**Expected Result:** ✅ No errors

### Test: Add Calendar Event
```bash
python3 << 'EOF'
from local_calendar import LocalCalendar
from datetime import datetime, timedelta

lc = LocalCalendar('test_calendar.db')
event_time = datetime.now() + timedelta(days=1)
lc.add_event('Test Meeting', event_time, event_time + timedelta(hours=1), 'Testing calendar')
print('✅ Calendar event added')
EOF
```

**Expected Result:** ✅ No errors, event added

### Test: Get Calendar Events
```bash
python3 << 'EOF'
from local_calendar import LocalCalendar
from datetime import datetime, timedelta

lc = LocalCalendar('test_calendar.db')
start_date = datetime.now()
end_date = start_date + timedelta(days=7)
events = lc.get_events(start_date=start_date, end_date=end_date)
print(f'✅ Found {len(events)} calendar events')
for event in events:
    print(f"  - {event['title']} on {event['start_time']}")
EOF
```

**Expected Result:** ✅ Shows events with titles and times

### Test: Calendar in Agent Context
**Test in Streamlit app:**
```
What's on my calendar?
Show me my calendar events
What do I have scheduled?
```

**Expected Results:**
- ✅ Agent mentions calendar events if any exist
- ✅ Shows upcoming events from local calendar
- ✅ Events displayed with dates/times

---

## 3. Reminder Service

### Test: Import and Initialize
```bash
python3 -c "from reminder_service import ReminderService; rs = ReminderService('test_reminders.db'); print('✅ Reminder Service imported and initialized')"
```

**Expected Result:** ✅ No errors

### Test: Add Reminder
```bash
python3 << 'EOF'
from reminder_service import ReminderService
from datetime import datetime, timedelta

rs = ReminderService('test_reminders.db')
reminder_time = datetime.now() + timedelta(minutes=5)
rs.add_reminder('Test Reminder', reminder_time, 'Testing reminder service')
print('✅ Reminder added')
EOF
```

**Expected Result:** ✅ No errors, reminder added

### Test: Get Pending Reminders
```bash
python3 << 'EOF'
from reminder_service import ReminderService
from datetime import datetime, timedelta

rs = ReminderService('test_reminders.db')
# Add a past reminder (should show as pending)
past_time = datetime.now() - timedelta(minutes=1)
rs.add_reminder('Past Reminder', past_time, 'Should be pending')
pending = rs.get_pending_reminders()
print(f'✅ Found {len(pending)} pending reminders')
for r in pending:
    print(f"  - {r['title']} (due: {r['reminder_time']})")
EOF
```

**Expected Result:** ✅ Shows pending reminders

### Test: Mark Reminder Completed
```bash
python3 << 'EOF'
from reminder_service import ReminderService
from datetime import datetime, timedelta

rs = ReminderService('test_reminders.db')
pending = rs.get_pending_reminders()
if pending:
    rs.mark_completed(pending[0]['id'])
    print(f'✅ Marked reminder {pending[0]["id"]} as completed')
    remaining = rs.get_pending_reminders()
    print(f'✅ Remaining pending reminders: {len(remaining)}')
else:
    print('⚠️ No pending reminders to mark')
EOF
```

**Expected Result:** ✅ Reminder marked completed, count decreases

### Test: Reminders in Agent Context
**Test in Streamlit app:**
```
What reminders do I have?
Show me my reminders
Any pending reminders?
```

**Expected Results:**
- ✅ Agent mentions reminders if any exist
- ✅ Shows pending reminders from local service
- ✅ Reminders displayed with due times

---

## 4. Task Service

### Test: Import and Initialize
```bash
python3 -c "from task_service import TaskService; ts = TaskService('test_tasks.db'); print('✅ Task Service imported and initialized')"
```

**Expected Result:** ✅ No errors

### Test: Add Task
```bash
python3 << 'EOF'
from task_service import TaskService
from datetime import datetime, timedelta

ts = TaskService('test_tasks.db')
due_date = datetime.now() + timedelta(days=3)
task_id = ts.add_task('Test Task', 'Testing task service', due_date, 'high')
print(f'✅ Task added with ID: {task_id}')
EOF
```

**Expected Result:** ✅ No errors, task ID returned

### Test: Get Pending Tasks
```bash
python3 << 'EOF'
from task_service import TaskService

ts = TaskService('test_tasks.db')
tasks = ts.get_pending_tasks()
print(f'✅ Found {len(tasks)} pending tasks')
for task in tasks:
    priority = task.get('priority', 'medium')
    due = task.get('due_date', 'No due date')
    print(f"  - [{priority.upper()}] {task['title']} (due: {due})")
EOF
```

**Expected Result:** ✅ Shows tasks with priorities and due dates

### Test: Get Overdue Tasks
```bash
python3 << 'EOF'
from task_service import TaskService
from datetime import datetime, timedelta

ts = TaskService('test_tasks.db')
# Add an overdue task
past_due = datetime.now() - timedelta(days=1)
ts.add_task('Overdue Task', 'This is overdue', past_due, 'high')
overdue = ts.get_overdue_tasks()
print(f'✅ Found {len(overdue)} overdue tasks')
for task in overdue:
    print(f"  - {task['title']} (was due: {task['due_date']})")
EOF
```

**Expected Result:** ✅ Shows overdue tasks

### Test: Update Task
```bash
python3 << 'EOF'
from task_service import TaskService

ts = TaskService('test_tasks.db')
tasks = ts.get_pending_tasks()
if tasks:
    task_id = tasks[0]['id']
    ts.update_task(task_id, priority='low', status='pending')
    print(f'✅ Updated task {task_id}')
    updated = ts.get_tasks()
    print(f'✅ Total tasks: {len(updated)}')
else:
    print('⚠️ No tasks to update')
EOF
```

**Expected Result:** ✅ Task updated successfully

### Test: Mark Task Completed
```bash
python3 << 'EOF'
from task_service import TaskService

ts = TaskService('test_tasks.db')
tasks = ts.get_pending_tasks()
if tasks:
    task_id = tasks[0]['id']
    ts.mark_completed(task_id)
    print(f'✅ Marked task {task_id} as completed')
    remaining = ts.get_pending_tasks()
    print(f'✅ Remaining pending tasks: {len(remaining)}')
else:
    print('⚠️ No tasks to complete')
EOF
```

**Expected Result:** ✅ Task marked completed, count decreases

### Test: Get Task Summary
```bash
python3 << 'EOF'
from task_service import TaskService

ts = TaskService('test_tasks.db')
summary = ts.get_task_summary()
print('✅ Task Summary:')
print(f"  Total Pending: {summary['total_pending']}")
print(f"  Overdue: {summary['overdue']}")
print(f"  High Priority: {summary['high_priority']}")
print(f"  Medium Priority: {summary['medium_priority']}")
print(f"  Low Priority: {summary['low_priority']}")
print(f"  Completed: {summary['completed']}")
EOF
```

**Expected Result:** ✅ Shows summary statistics

### Test: Tasks in Agent Context
**Test in Streamlit app:**
```
What tasks do I have?
Show me my tasks
What do I need to do?
Any overdue tasks?
```

**Expected Results:**
- ✅ Agent mentions tasks if any exist
- ✅ Shows pending tasks with priorities
- ✅ Highlights overdue tasks
- ✅ Tasks displayed with due dates

---

## 5. Agent Integration

### Test: Agent Creation with Local Services
```bash
python3 << 'EOF'
from mo11y_agent import create_mo11y_agent

try:
    agent = create_mo11y_agent(db_path='test_agent.db')
    print('✅ Agent created successfully')
    print(f'  Local Calendar: {hasattr(agent, "local_calendar")}')
    print(f'  Reminder Service: {hasattr(agent, "reminder_service")}')
    print(f'  Task Service: {hasattr(agent, "task_service")}')
except Exception as e:
    print(f'❌ Error: {e}')
EOF
```

**Expected Results:**
- ✅ Agent created without errors
- ✅ All three local services are present
- ✅ All return `True`

### Test: Agent Context Includes Local Services
**Test in Streamlit app:**
```
What's on my calendar and what tasks do I have?
Show me everything I need to do today
```

**Expected Results:**
- ✅ Agent mentions calendar events if any
- ✅ Agent mentions reminders if any
- ✅ Agent mentions tasks if any
- ✅ All information comes from local services

### Test: Action Detection
**Test in Streamlit app:**
```
Schedule a meeting tomorrow at 2pm
Remind me to call mom at 6pm
Add a task to finish the report by Friday
```

**Expected Results:**
- ✅ Agent detects calendar action
- ✅ Agent detects reminder action
- ✅ Agent detects task action
- ✅ Agent provides instructions on how to use local services

---

## 6. Conversation Timestamps

### Test: Timestamps in Messages
**Test in Streamlit app:**
1. Send any message
2. Check if timestamp appears above your message
3. Wait for response
4. Check if timestamp appears above agent response

**Expected Results:**
- ✅ User messages have timestamps displayed
- ✅ Agent messages have timestamps displayed
- ✅ Timestamp format: `YYYY-MM-DD HH:MM:SS`
- ✅ Timestamps appear in lighter color (70% opacity)

### Test: Timestamp Format
```bash
python3 -c "import datetime; print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))"
```

**Expected Result:** ✅ Format matches: `2025-12-29 14:33:55`

---

## 7. Database Operations

### Test: Database Tables Exist
```bash
python3 << 'EOF'
import sqlite3

db_path = 'SPOHNZ.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

required_tables = [
    'calendar_events',
    'reminders',
    'tasks',
    'episodic_memories',
    'semantic_memories'
]

print('✅ Database Tables:')
for table in required_tables:
    if table in tables:
        print(f"  ✅ {table}")
    else:
        print(f"  ❌ {table} - MISSING")

conn.close()
EOF
```

**Expected Result:** ✅ All required tables exist

### Test: Database Schema
```bash
python3 << 'EOF'
import sqlite3

db_path = 'SPOHNZ.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

tables = ['calendar_events', 'reminders', 'tasks']
for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    print(f'\n✅ {table} columns:')
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

conn.close()
EOF
```

**Expected Result:** ✅ All tables have correct schema

---

## 8. Conversation Logging

### Test: Log Directory Exists
```bash
ls -la conversation_logs/ 2>/dev/null && echo "✅ Log directory exists" || echo "❌ Log directory missing"
```

**Expected Result:** ✅ Directory exists

### Test: Log Files Created
**Test in Streamlit app:**
1. Have a conversation with any persona
2. Check if log file was created

```bash
ls -lt conversation_logs/*.txt | head -1
```

**Expected Result:** ✅ Most recent log file exists

### Test: Log File Content
```bash
python3 << 'EOF'
import os
import glob

log_files = glob.glob('conversation_logs/*.txt')
if log_files:
    latest = max(log_files, key=os.path.getmtime)
    print(f'✅ Latest log file: {latest}')
    with open(latest, 'r') as f:
        content = f.read()
        if 'EXCHANGE #' in content:
            print('✅ Log contains conversation exchanges')
        if 'USER INPUT:' in content:
            print('✅ Log contains user input')
        if 'AGENT RESPONSE:' in content:
            print('✅ Log contains agent response')
else:
    print('⚠️ No log files found')
EOF
```

**Expected Result:** ✅ Log file contains expected content

---

## 9. Comprehensive Integration Test

### Test: All Services Work Together
```bash
python3 << 'EOF'
from local_calendar import LocalCalendar
from reminder_service import ReminderService
from task_service import TaskService
from datetime import datetime, timedelta

db_path = 'test_integration.db'

# Initialize all services
lc = LocalCalendar(db_path)
rs = ReminderService(db_path)
ts = TaskService(db_path)

# Add test data
now = datetime.now()
lc.add_event('Test Event', now + timedelta(days=1), now + timedelta(days=1, hours=1), 'Test')
rs.add_reminder('Test Reminder', now + timedelta(hours=2), 'Test')
ts.add_task('Test Task', 'Test', now + timedelta(days=2), 'high')

# Verify all data
events = lc.get_events()
reminders = rs.get_pending_reminders()
tasks = ts.get_pending_tasks()

print('✅ Integration Test Results:')
print(f'  Calendar Events: {len(events)}')
print(f'  Pending Reminders: {len(reminders)}')
print(f'  Pending Tasks: {len(tasks)}')

if len(events) > 0 and len(reminders) > 0 and len(tasks) > 0:
    print('✅ All services working together!')
else:
    print('❌ Some services failed')
EOF
```

**Expected Result:** ✅ All services work together

---

## 10. End-to-End Test in Streamlit

### Full Conversation Test
**Test in Streamlit app:**

1. **Time Question:**
   ```
   What time is it?
   ```
   ✅ Should answer immediately with current time

2. **Calendar Query:**
   ```
   What's on my calendar?
   ```
   ✅ Should show calendar events from local calendar

3. **Add Calendar Event:**
   ```
   Schedule a meeting tomorrow at 2pm called Team Standup
   ```
   ✅ Should detect calendar action

4. **Reminder Query:**
   ```
   What reminders do I have?
   ```
   ✅ Should show reminders from local service

5. **Add Reminder:**
   ```
   Remind me to call mom at 6pm
   ```
   ✅ Should detect reminder action

6. **Task Query:**
   ```
   What tasks do I have?
   ```
   ✅ Should show tasks from local service

7. **Add Task:**
   ```
   Add a high priority task to finish the report by Friday
   ```
   ✅ Should detect task action

8. **Check Timestamps:**
   - Look at all messages
   - ✅ All should have timestamps

9. **Check Logs:**
   ```bash
   ls -lt conversation_logs/*.txt | head -1
   ```
   ✅ Latest log file should exist

---

## Quick Test Script

Save this as `quick_test.sh`:

```bash
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
conn = sqlite3.connect('SPOHNZ.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
required = ['calendar_events', 'reminders', 'tasks']
missing = [t for t in required if t not in tables]
if missing:
    print(f'❌ Missing tables: {missing}')
else:
    print('✅ All required tables exist')
conn.close()
EOF

# Test 5: Log directory
echo ""
echo "5. Testing log directory..."
if [ -d "conversation_logs" ]; then
    echo "✅ Log directory exists"
else
    echo "❌ Log directory missing"
fi

echo ""
echo "=========================="
echo "✅ Quick test complete!"
```

Make it executable:
```bash
chmod +x quick_test.sh
```

Run it:
```bash
./quick_test.sh
```

---

## Troubleshooting

### If tests fail:

1. **Import Errors:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Errors:**
   ```bash
   # Check if database exists
   ls -la *.db
   
   # Check database permissions
   ls -l *.db
   ```

3. **Service Not Found:**
   ```bash
   # Verify files exist
   ls -la local_calendar.py reminder_service.py task_service.py
   ```

4. **Agent Creation Fails:**
   ```bash
   # Check if Ollama is running (for full agent test)
   ollama ps
   
   # Or test without Ollama (imports only)
   python3 -c "from mo11y_agent import Mo11yAgent; print('✅ Agent class available')"
   ```

---

## Test After Changes Checklist

After making any changes, run through this checklist:

- [ ] Run `quick_test.sh` (all tests pass)
- [ ] Test simple questions in Streamlit (time/date)
- [ ] Test calendar operations (add/view events)
- [ ] Test reminder operations (add/view reminders)
- [ ] Test task operations (add/view/complete tasks)
- [ ] Test agent integration (agent sees all local data)
- [ ] Test timestamps (appear on all messages)
- [ ] Test conversation logging (logs are created)
- [ ] Test database (all tables exist and work)

---

## Notes

- All tests use test databases (`test_*.db`) to avoid affecting production data
- Streamlit tests require the app to be running: `streamlit run app_enhanced.py`
- Some tests require Ollama to be running for full agent functionality
- Database path can be changed in `config.json` (`db_path`)

---

**Last Tested**: [Update this date after testing]
**Tested By**: [Your name]
**Results**: [Pass/Fail notes]
