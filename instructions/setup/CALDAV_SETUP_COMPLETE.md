# CalDAV Setup Complete Guide

## ✅ Startup Order

**Yes, you're correct!** Here's the proper startup order:

1. **Start MCP Server** (Terminal 1):
   ```bash
   python3 local_mcp_server.py
   ```
   Should show: `Uvicorn running on http://0.0.0.0:8443`

2. **Start Streamlit App** (Terminal 2):
   ```bash
   streamlit run app_enhanced.py
   ```

3. **Start CalDAV Server** (Terminal 3, if using local):
   ```bash
   # Option 1: Radicale (simplest)
   pip install radicale
   radicale
   # Runs on http://localhost:5232/
   
   # Option 2: Baikal (recommended - has web UI)
   ./run_baikal.sh
   # Runs on http://localhost:8080/
   ```

## ✅ Alex Mercer Can Add/Delete Events

I've added the functionality! Alex Mercer can now:

- **Add events**: "Add a meeting tomorrow at 2pm"
- **Delete events**: "Delete the meeting on Friday"
- **View events**: "What's on my calendar?"

The agent will automatically use these functions when you ask.

## 📅 Viewing Your Calendar

### Option 1: Baikal Web UI (Recommended)

Baikal has a built-in web calendar interface:

```bash
# Start Baikal
./run_baikal.sh

# Access web UI at:
http://localhost:8080/
# Default login: admin/admin
```

**Features:**
- Full calendar view (month/week/day)
- Add/edit/delete events via web UI
- Syncs with CalDAV clients
- Beautiful interface

### Option 2: Radicale + External Client

Radicale doesn't have a web UI, but you can use:

**Thunderbird** (Free):
- Install Thunderbird
- Add Calendar → Network Calendar
- URL: `http://localhost:5232/dav/calendars/USERNAME/CALENDARNAME/`

**Evolution** (Linux):
- Calendar → New Calendar → CalDAV
- URL: `http://localhost:5232/dav/calendars/USERNAME/CALENDARNAME/`

**DAVx⁵** (Android):
- Add account → CalDAV
- Server: `http://YOUR_IP:5232/`

### Option 3: Nextcloud (Full Solution)

Nextcloud has a complete web UI:

```bash
docker run -d -p 8080:80 --name nextcloud nextcloud
# Access at http://localhost:8080/
```

## 🚀 Quick Setup Steps

### 1. Install CalDAV Server

**Recommended: Baikal** (has web UI):
```bash
# Check if run_baikal.sh exists
ls run_baikal.sh

# If not, create it or run manually:
docker run -d -p 8080:80 --name baikal ckulka/baikal:nginx
```

### 2. Configure CalDAV in Mo11y

```bash
python3 setup_caldav.py
```

Enter:
- **URL**: `http://localhost:8080/cal.php/calendars/YOUR_USERNAME/YOUR_CALENDAR/` (Baikal)
- **URL**: `http://localhost:5232/` (Radicale)
- **Username**: Your CalDAV username
- **Password**: Your CalDAV password
- **Calendar name**: "personal" (or your calendar name)

### 3. Test It

Ask Alex Mercer:
- "What's on my calendar?"
- "Add a meeting tomorrow at 2pm called 'Team Standup'"
- "Show me my calendar events"

### 4. View in Web UI

**If using Baikal:**
- Open: http://localhost:8080/
- Login with your credentials
- See your calendar with all events!

## 📋 Example Usage

```
You: "Add a dentist appointment next Friday at 10am"
Alex Mercer: [Adds event] "I've added 'Dentist appointment' to your calendar for next Friday at 10am."

You: "What's on my calendar this week?"
Alex Mercer: [Reads events] "You have 3 events this week: ..."

You: "Delete the dentist appointment"
Alex Mercer: [Deletes event] "I've removed the dentist appointment from your calendar."
```

## 🔧 Requirements

Make sure you have:
```bash
pip install caldav icalendar
```

## 🎯 Summary

✅ **Startup Order**: MCP Server → Streamlit → CalDAV Server  
✅ **Add/Delete**: Alex Mercer can add and delete events  
✅ **View Calendar**: Use Baikal web UI (http://localhost:8080/) or external client  

**Best Option**: Use Baikal - it has a web UI so you can see your calendar in a nice calendar form!
