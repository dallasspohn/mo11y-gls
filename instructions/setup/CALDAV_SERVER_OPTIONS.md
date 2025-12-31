# Local CalDAV Server Options

## Quick Recommendations

### 1. **Radicale** ⭐ Easiest
**Best for:** Quick local setup, minimal configuration
- **Install:** `pip install radicale`
- **Run:** `radicale`
- **Default URL:** `http://localhost:5232/`
- **Pros:** Simple, Python-based, no database needed
- **Cons:** Basic features, single user by default

**Quick Start:**
```bash
pip install radicale
radicale
# Access at http://localhost:5232/
```

### 2. **Baikal** ⭐ Recommended
**Best for:** Full-featured, production-ready
- **Install:** Docker or PHP
- **Run:** Docker: `docker run -d -p 8080:80 ckulka/baikal:nginx` (port 8080 to avoid conflicts)
- **Default URL:** `http://localhost:8080/`
- **Pros:** Full CalDAV/CardDAV, web UI, multi-user
- **Cons:** Requires Docker or PHP setup

**Quick Start (Docker):**
```bash
# Use the helper script (recommended)
./run_baikal.sh

# Or manually:
docker run -d -p 8080:80 --name baikal ckulka/baikal:nginx
# Access at http://localhost:8080/
# Default login: admin/admin
```

### 3. **Nextcloud** (Full-featured)
**Best for:** Complete solution with calendar, contacts, files
- **Install:** Docker or manual
- **Run:** Docker: `docker run -d -p 8080:80 nextcloud`
- **Default URL:** `http://localhost:8080/remote.php/dav/calendars/`
- **Pros:** Full cloud solution, web UI, many features
- **Cons:** More resource-intensive

**Quick Start (Docker):**
```bash
docker run -d -p 8080:80 --name nextcloud nextcloud
# Access at http://localhost:8080/
```

### 4. **DAViCal** (PostgreSQL-based)
**Best for:** Multi-user, enterprise features
- **Install:** Package manager or Docker
- **Run:** Requires PostgreSQL setup
- **Pros:** Powerful, scalable
- **Cons:** More complex setup

## Comparison

| Server | Setup Time | Port | Features | Best For |
|--------|------------|------|----------|----------|
| **Radicale** | 2 min | 5232 | Basic | Quick testing |
| **Baikal** | 5 min | 8080 | Full | Production use |
| **Nextcloud** | 10 min | 8080 | Complete | Full solution |
| **DAViCal** | 15 min | 80/443 | Enterprise | Multi-user |

## Recommendation

**Start with Radicale** for quick testing:
```bash
pip install radicale
radicale
```

Then use `setup_caldav.py` with:
- URL: `http://localhost:5232/`
- Username: (your username)
- Password: (your password)

**For production, use Baikal** - it's more feature-complete but still simple:
```bash
./run_baikal.sh
# Access at http://localhost:8080/
# Then use setup_caldav.py with URL: http://localhost:8080/cal.php/calendars/YOUR_USERNAME/YOUR_CALENDAR/
```

## Testing Your Server

Once your server is running, test with:
```bash
python3 setup_caldav.py
```

Or test manually:
```python
from external_apis import ExternalAPIManager

api = ExternalAPIManager("mo11y_companion.db")
api.register_caldav_calendar(
    url="http://localhost:5232/",
    username="your_username",
    password="your_password"
)

events = api.get_calendar_events(days_ahead=7)
print(f"Found {len(events)} events")
```

## Common Issues

1. **Connection refused:** Make sure server is running
2. **Authentication failed:** Check username/password
3. **No calendars found:** Create a calendar first (usually via web UI)
4. **URL format:** Make sure URL ends with `/`

## Next Steps

1. Choose a server (Radicale for quick start)
2. Install and run it
3. Create a calendar (usually via web UI)
4. Run `python3 setup_caldav.py`
5. Test by asking Mo11y: "What's on my calendar?"
