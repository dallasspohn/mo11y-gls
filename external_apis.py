"""
External API Integration System for Mo11y
Integrates with external services like calendar, notes, weather, etc.
"""

import json
import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import sqlite3
import base64
from io import BytesIO


class ExternalAPIManager:
    """
    Manages integrations with external APIs
    Supports: Calendar, Notes, Weather, Email, etc.
    """
    
    def __init__(self, db_path: str = "mo11y_companion.db"):
        # Normalize the path (expand user dir, make absolute)
        self.db_path = os.path.abspath(os.path.expanduser(db_path))
        self.api_configs = {}
        self.init_api_db()
        self.load_configs()
    
    def init_api_db(self):
        """Initialize database for API configurations and cache"""
        # Ensure the directory exists before connecting
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # API configurations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_configurations (
                api_name TEXT PRIMARY KEY,
                api_type TEXT NOT NULL,
                config_json TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                last_used DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # API call cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_cache (
                cache_key TEXT PRIMARY KEY,
                api_name TEXT NOT NULL,
                response_data TEXT NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # API call history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_call_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_name TEXT NOT NULL,
                endpoint TEXT,
                method TEXT,
                status_code INTEGER,
                response_time_ms INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def load_configs(self):
        """Load API configurations from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT api_name, api_type, config_json, enabled FROM api_configurations")
        rows = cursor.fetchall()
        
        for row in rows:
            self.api_configs[row[0]] = {
                'type': row[1],
                'config': json.loads(row[2]),
                'enabled': bool(row[3])
            }
        
        conn.close()
    
    def register_api(self, api_name: str, api_type: str, config: Dict, enabled: bool = True):
        """Register a new API configuration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO api_configurations
            (api_name, api_type, config_json, enabled)
            VALUES (?, ?, ?, ?)
        """, (api_name, api_type, json.dumps(config), enabled))
        
        conn.commit()
        conn.close()
        
        self.api_configs[api_name] = {
            'type': api_type,
            'config': config,
            'enabled': enabled
        }
    
    def register_weather_api(self, api_key: str, provider: str = "openweathermap", 
                             default_location: str = "Crandall, TX"):
        """
        Register weather API - Easy setup helper
        
        Args:
            api_key: API key from weather service
            provider: "openweathermap" or "weather_api"
            default_location: Default location for weather queries
        """
        self.register_api("weather", provider, {
            "api_key": api_key,
            "default_location": default_location
        })
    
    def register_google_calendar(self, credentials_path: str = "credentials.json",
                                 token_path: str = "token.json",
                                 calendar_id: str = "primary"):
        """
        Register Google Calendar - Easy setup helper
        
        Args:
            credentials_path: Path to Google OAuth2 credentials JSON file
            token_path: Path to store OAuth2 token (will be created after first auth)
            calendar_id: Calendar ID to use (default: "primary" for main calendar)
        """
        self.register_api("calendar", "google_calendar", {
            "credentials_path": credentials_path,
            "token_path": token_path,
            "calendar_id": calendar_id
        })
    
    def _log_api_call(self, api_name: str, endpoint: str, method: str,
                     status_code: int, response_time_ms: int):
        """Log API call for monitoring"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO api_call_history
            (api_name, endpoint, method, status_code, response_time_ms)
            VALUES (?, ?, ?, ?, ?)
        """, (api_name, endpoint, method, status_code, response_time_ms))
        
        # Update last_used
        cursor.execute("""
            UPDATE api_configurations
            SET last_used = CURRENT_TIMESTAMP
            WHERE api_name = ?
        """, (api_name,))
        
        conn.commit()
        conn.close()
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached API response if not expired"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT response_data, expires_at
            FROM api_cache
            WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP
        """, (cache_key,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None
    
    def _cache_response(self, cache_key: str, api_name: str, response_data: Dict,
                        cache_ttl_seconds: int = 300):
        """Cache API response"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(seconds=cache_ttl_seconds)
        
        cursor.execute("""
            INSERT OR REPLACE INTO api_cache
            (cache_key, api_name, response_data, expires_at)
            VALUES (?, ?, ?, ?)
        """, (cache_key, api_name, json.dumps(response_data), expires_at.isoformat()))
        
        conn.commit()
        conn.close()
    
    # Calendar Integration
    def list_calendars(self) -> List[Dict]:
        """List all available Google Calendars"""
        api_name = "calendar"
        if api_name not in self.api_configs or not self.api_configs[api_name]['enabled']:
            return []
        
        config = self.api_configs[api_name]['config']
        api_type = self.api_configs[api_name]['type']
        
        if api_type != "google_calendar":
            return []
        
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            import os.path
        except ImportError:
            return []
        
        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        
        credentials_path = config.get('credentials_path', 'credentials.json')
        token_path = config.get('token_path', 'token.json')
        
        if not os.path.exists(credentials_path):
            return []
        
        creds = None
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except:
                pass
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except:
                    return []
            else:
                return []
        
        try:
            service = build('calendar', 'v3', credentials=creds)
            calendar_list = service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            
            result = []
            for cal in calendars:
                result.append({
                    'id': cal.get('id', ''),
                    'summary': cal.get('summary', 'No name'),
                    'primary': cal.get('primary', False),
                    'description': cal.get('description', ''),
                    'accessRole': cal.get('accessRole', '')
                })
            
            return result
        except Exception as e:
            print(f"Error listing calendars: {e}")
            return []
    
    def get_calendar_events(self, days_ahead: int = 7) -> List[Dict]:
        """Get calendar events for the next N days"""
        # This is a template - implement based on your calendar API
        # Examples: Google Calendar, Outlook, etc.
        
        api_name = "calendar"
        if api_name not in self.api_configs or not self.api_configs[api_name]['enabled']:
            return []
        
        cache_key = f"calendar_events_{days_ahead}"
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached
        
        config = self.api_configs[api_name]['config']
        api_type = self.api_configs[api_name]['type']
        
        try:
            start_time = datetime.now()
            
            if api_type == "google_calendar":
                events = self._get_google_calendar_events(config, days_ahead)
            else:
                events = []
            
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self._log_api_call(api_name, "events", "GET", 200, response_time)
            
            self._cache_response(cache_key, api_name, events, cache_ttl_seconds=300)
            return events
            
        except Exception as e:
            self._log_api_call(api_name, "events", "GET", 500, 0)
            return []
    
    def _get_google_calendar_events(self, config: Dict, days_ahead: int) -> List[Dict]:
        """Get events from Google Calendar API"""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            import os.path
        except ImportError:
            print("Google Calendar libraries not installed. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            return []
        
        # Use readonly scope for reading events (safer)
        # Note: Token must be created with both readonly and write scopes
        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        
        credentials_path = config.get('credentials_path', 'credentials.json')
        token_path = config.get('token_path', 'token.json')
        calendar_id = config.get('calendar_id', 'primary')
        
        if not os.path.exists(credentials_path):
            print(f"Google Calendar credentials not found at {credentials_path}")
            print("Please run setup_google_calendar.py to set up OAuth2")
            return []
        
        creds = None
        # Load existing token if available
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception as e:
                print(f"Error loading token: {e}")
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    # Check if it's a scope mismatch error
                    error_str = str(e)
                    if 'invalid_scope' in error_str or 'Bad Request' in error_str:
                        print(f"⚠️ Token scope mismatch. Please re-authenticate by running: python3 setup_google_calendar.py")
                        print(f"   Error details: {e}")
                    else:
                        print(f"Error refreshing token: {e}")
                    return []
            else:
                print("Google Calendar token expired or invalid. Please run setup_google_calendar.py to re-authenticate")
                return []
            
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        try:
            service = build('calendar', 'v3', credentials=creds)
            
            # Get events for the next N days
            now = datetime.utcnow().isoformat() + 'Z'
            time_max = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
            
            try:
                events_result = service.events().list(
                    calendarId=calendar_id,
                    timeMin=now,
                    timeMax=time_max,
                    maxResults=50,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
            except Exception as calendar_error:
                error_str = str(calendar_error)
                # Check for 404 Not Found error
                if '404' in error_str or 'notFound' in error_str.lower():
                    print(f"⚠️ Calendar '{calendar_id}' not found!")
                    print(f"   The calendar ID '{calendar_id}' doesn't exist or isn't accessible.")
                    print(f"   Trying 'primary' calendar instead...")
                    
                    # Try with 'primary' calendar
                    try:
                        events_result = service.events().list(
                            calendarId='primary',
                            timeMin=now,
                            timeMax=time_max,
                            maxResults=50,
                            singleEvents=True,
                            orderBy='startTime'
                        ).execute()
                        print(f"   ✅ Successfully using 'primary' calendar")
                        
                        # Update config to use 'primary' for next time
                        try:
                            config['calendar_id'] = 'primary'
                            self.register_api("calendar", "google_calendar", config)
                            print(f"   💾 Updated calendar ID to 'primary' in database")
                        except:
                            pass
                    except Exception as primary_error:
                        print(f"   ❌ Error accessing 'primary' calendar: {primary_error}")
                        print(f"\n   To fix this:")
                        print(f"   1. Run: python3 setup_google_calendar.py")
                        print(f"   2. When asked for calendar ID, use 'primary' or list your calendars")
                        return []
                else:
                    raise calendar_error
            
            events = events_result.get('items', [])
            
            result = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                result.append({
                    'title': event.get('summary', 'No title'),
                    'start': start,
                    'end': end,
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                    'id': event.get('id', '')
                })
            
            return result
            
        except Exception as e:
            print(f"Google Calendar API error: {e}")
            return []
    
    
    def add_calendar_event(self, title: str, start: datetime, end: datetime = None, 
                          description: str = "", location: str = "") -> bool:
        """Add an event to Google Calendar"""
        api_name = "calendar"
        if api_name not in self.api_configs or not self.api_configs[api_name]['enabled']:
            return False
        
        api_type = self.api_configs[api_name]['type']
        config = self.api_configs[api_name]['config']
        
        if api_type == "google_calendar":
            return self._add_google_calendar_event(config, title, start, end, description, location)
        
        return False
    
    def _add_google_calendar_event(self, config: Dict, title: str, start: datetime, 
                                   end: datetime = None, description: str = "", location: str = "") -> bool:
        """Add event to Google Calendar"""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            import os.path
        except ImportError:
            print("Google Calendar libraries not installed. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            return False
        
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        
        credentials_path = config.get('credentials_path', 'credentials.json')
        token_path = config.get('token_path', 'token.json')
        calendar_id = config.get('calendar_id', 'primary')
        
        if not os.path.exists(credentials_path):
            print(f"Google Calendar credentials not found at {credentials_path}")
            return False
        
        creds = None
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception as e:
                print(f"Error loading token: {e}")
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    return False
            else:
                print("Google Calendar token expired or invalid. Please run setup_google_calendar.py to re-authenticate")
                return False
            
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        try:
            service = build('calendar', 'v3', credentials=creds)
            
            if not end:
                end = start + timedelta(hours=1)
            
            # Format datetime for Google Calendar API
            start_str = start.isoformat()
            end_str = end.isoformat()
            
            event = {
                'summary': title,
                'start': {
                    'dateTime': start_str,
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_str,
                    'timeZone': 'UTC',
                },
            }
            
            if description:
                event['description'] = description
            if location:
                event['location'] = location
            
            event = service.events().insert(calendarId=calendar_id, body=event).execute()
            return True
            
        except Exception as e:
            print(f"Google Calendar add event error: {e}")
            return False
    
    def delete_calendar_event(self, event_title: str, start_date: datetime = None, event_id: str = None) -> bool:
        """Delete an event from Google Calendar"""
        api_name = "calendar"
        if api_name not in self.api_configs or not self.api_configs[api_name]['enabled']:
            return False
        
        api_type = self.api_configs[api_name]['type']
        config = self.api_configs[api_name]['config']
        
        if api_type == "google_calendar":
            return self._delete_google_calendar_event(config, event_title, start_date, event_id)
        
        return False
    
    def _delete_google_calendar_event(self, config: Dict, event_title: str, 
                                     start_date: datetime = None, event_id: str = None) -> bool:
        """Delete event from Google Calendar"""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            import os.path
        except ImportError:
            print("Google Calendar libraries not installed. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            return False
        
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        
        credentials_path = config.get('credentials_path', 'credentials.json')
        token_path = config.get('token_path', 'token.json')
        calendar_id = config.get('calendar_id', 'primary')
        
        if not os.path.exists(credentials_path):
            print(f"Google Calendar credentials not found at {credentials_path}")
            return False
        
        creds = None
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception as e:
                print(f"Error loading token: {e}")
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    return False
            else:
                print("Google Calendar token expired or invalid. Please run setup_google_calendar.py to re-authenticate")
                return False
            
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        try:
            service = build('calendar', 'v3', credentials=creds)
            
            # If event_id is provided, use it directly
            if event_id:
                try:
                    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
                    return True
                except Exception as e:
                    print(f"Error deleting event by ID: {e}")
                    return False
            
            # Otherwise, search for events matching the title
            now = datetime.utcnow().isoformat() + 'Z'
            time_max = (datetime.utcnow() + timedelta(days=365)).isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=now,
                timeMax=time_max,
                maxResults=50,
                singleEvents=True,
                orderBy='startTime',
                q=event_title
            ).execute()
            
            events = events_result.get('items', [])
            
            # Find matching event
            for event in events:
                summary = event.get('summary', '')
                if event_title.lower() in summary.lower():
                    # Check date if provided
                    if start_date:
                        event_start_str = event['start'].get('dateTime', event['start'].get('date'))
                        event_start = datetime.fromisoformat(event_start_str.replace('Z', '+00:00'))
                        if event_start.date() == start_date.date():
                            service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
                            return True
                    else:
                        # Delete first match if no date specified
                        service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
                        return True
            
            return False
            
        except Exception as e:
            print(f"Google Calendar delete event error: {e}")
            return False
    
    # Notes Integration
    def get_notes(self, limit: int = 10) -> List[Dict]:
        """Get recent notes"""
        api_name = "notes"
        if api_name not in self.api_configs or not self.api_configs[api_name]['enabled']:
            return []
        
        cache_key = f"notes_{limit}"
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached
        
        config = self.api_configs[api_name]['config']
        api_type = self.api_configs[api_name]['type']
        
        try:
            start_time = datetime.now()
            
            if api_type == "obsidian":
                notes = self._get_obsidian_notes(config, limit)
            elif api_type == "joplin":
                notes = self._get_joplin_notes(config, limit)
            else:
                notes = []
            
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self._log_api_call(api_name, "notes", "GET", 200, response_time)
            
            self._cache_response(cache_key, api_name, notes, cache_ttl_seconds=600)
            return notes
            
        except Exception as e:
            self._log_api_call(api_name, "notes", "GET", 500, 0)
            return []
    
    def _get_obsidian_notes(self, config: Dict, limit: int) -> List[Dict]:
        """Get notes from Obsidian vault"""
        vault_path = config.get('vault_path')
        if not vault_path or not os.path.exists(vault_path):
            return []
        
        notes = []
        for root, dirs, files in os.walk(vault_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            notes.append({
                                'title': file.replace('.md', ''),
                                'content': content[:500],  # First 500 chars
                                'path': file_path,
                                'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                            })
                    except:
                        continue
                    
                    if len(notes) >= limit:
                        break
            if len(notes) >= limit:
                break
        
        return notes
    
    def _get_joplin_notes(self, config: Dict, limit: int) -> List[Dict]:
        """Get notes from Joplin API"""
        # Requires Joplin API token
        # See: https://joplinapp.org/api/
        return []
    
    # Weather Integration
    def get_weather(self, location: str = None) -> Optional[Dict]:
        """Get weather information"""
        api_name = "weather"
        if api_name not in self.api_configs or not self.api_configs[api_name]['enabled']:
            return None
        
        cache_key = f"weather_{location or 'default'}"
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached
        
        config = self.api_configs[api_name]['config']
        api_type = self.api_configs[api_name]['type']
        
        try:
            start_time = datetime.now()
            
            if api_type == "openweathermap":
                weather = self._get_openweathermap(config, location)
            elif api_type == "weather_api":
                weather = self._get_weather_api(config, location)
            else:
                weather = None
            
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self._log_api_call(api_name, "current", "GET", 200 if weather else 500, response_time)
            
            if weather:
                self._cache_response(cache_key, api_name, weather, cache_ttl_seconds=600)
            return weather
            
        except Exception as e:
            self._log_api_call(api_name, "current", "GET", 500, 0)
            return None
    
    def _get_openweathermap(self, config: Dict, location: str = None) -> Optional[Dict]:
        """Get weather from OpenWeatherMap API"""
        api_key = config.get('api_key')
        if not api_key:
            return None
        
        location = location or config.get('default_location', 'Crandall, TX')
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': location,
            'appid': api_key,
            'units': 'imperial'
        }
        
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'location': data.get('name', location),
                'temperature': data['main']['temp'],
                'feels_like': data['main'].get('feels_like', data['main']['temp']),
                'description': data['weather'][0]['description'],
                'humidity': data['main']['humidity'],
                'wind_speed': data.get('wind', {}).get('speed', 0)
            }
        return None
    
    def _get_weather_api(self, config: Dict, location: str = None) -> Optional[Dict]:
        """Get weather from weather-api.com"""
        api_key = config.get('api_key')
        if not api_key:
            return None
        
        location = location or config.get('default_location', 'Crandall, TX')
        url = "https://api.weatherapi.com/v1/current.json"
        params = {
            'key': api_key,
            'q': location
        }
        
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'location': f"{data['location']['name']}, {data['location']['region']}",
                'temperature': data['current']['temp_f'],
                'feels_like': data['current']['feelslike_f'],
                'description': data['current']['condition']['text'],
                'humidity': data['current']['humidity'],
                'wind_speed': data['current']['wind_mph']
            }
        return None
    
    def register_huggingface_image_api(self, api_token: str = None):
        """
        Register Hugging Face Inference API for image generation
        
        Uses FREE models that don't require payment:
        - runwayml/stable-diffusion-v1-5 (free, good quality)
        - stabilityai/stable-diffusion-2-1 (free alternative)
        
        Args:
            api_token: Hugging Face API token (optional, but recommended for higher rate limits)
        """
        # Use free Stable Diffusion model instead of paid FLUX
        self.register_api("huggingface_image", "huggingface_inference", {
            "api_token": api_token,
            "model": "runwayml/stable-diffusion-v1-5"  # FREE model - no payment required
        })
    
    def generate_image(self, prompt: str, style: str = "default", 
                      negative_prompt: str = None, num_inference_steps: int = 28,
                      guidance_scale: float = 3.5, width: int = 1024, height: int = 1024) -> Optional[str]:
        """
        Generate an image using FREE Stable Diffusion via Hugging Face Inference API
        
        Uses runwayml/stable-diffusion-v1-5 (free, no payment required)
        
        Args:
            prompt: Text description of the image to generate
            style: Style preset (default, artistic, realistic, etc.) - not used in FLUX but kept for compatibility
            negative_prompt: What to avoid in the image
            num_inference_steps: Number of denoising steps (default: 28)
            guidance_scale: How closely to follow the prompt (default: 3.5)
            width: Image width in pixels (default: 1024)
            height: Image height in pixels (default: 1024)
        
        Returns:
            Path to saved image file, or None if generation failed
        """
        api_name = "huggingface_image"
        if api_name not in self.api_configs or not self.api_configs[api_name]['enabled']:
            # Try to auto-register if not configured
            self.register_huggingface_image_api()
            if api_name not in self.api_configs:
                return None
        
        config = self.api_configs[api_name]['config']
        api_token = config.get('api_token')
        # Use free Stable Diffusion model (no payment required)
        model = config.get('model', "runwayml/stable-diffusion-v1-5")
        
        try:
            from huggingface_hub import InferenceClient
            
            print(f"DEBUG [generate_image]: Initializing Hugging Face InferenceClient")
            print(f"DEBUG [generate_image]: Model: {model}")
            print(f"DEBUG [generate_image]: API token present: {bool(api_token)}")
            print(f"DEBUG [generate_image]: Prompt: {prompt[:100]}...")
            
            # Initialize client
            client = InferenceClient(token=api_token) if api_token else InferenceClient()
            
            # Prepare parameters for Stable Diffusion API
            # Note: Stable Diffusion API uses different parameter names
            parameters = {
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
            }
            
            # Only include width/height if model supports it (some models don't)
            # Stable Diffusion v1.5 supports these, but we'll let the API handle defaults if needed
            if width != 1024 or height != 1024:
                parameters["width"] = width
                parameters["height"] = height
            
            if negative_prompt:
                parameters["negative_prompt"] = negative_prompt
            
            print(f"DEBUG [generate_image]: Calling text_to_image API...")
            # Generate image - use direct API call for Stable Diffusion
            try:
                # Try the text_to_image method first
                image_bytes = client.text_to_image(
                    model=model,
                    prompt=prompt,
                    **parameters
                )
                print(f"DEBUG [generate_image]: API call successful, received {len(image_bytes)} bytes")
            except (StopIteration, AttributeError, Exception) as e:
                # Fallback: Use direct HTTP API call (requests already imported)
                print(f"DEBUG [generate_image]: text_to_image method failed ({e}), trying direct API call...")
                
                api_url = f"https://router.huggingface.co/models/{model}"
                headers = {"Content-Type": "application/json"}
                if api_token:
                    headers["Authorization"] = f"Bearer {api_token}"
                
                # Stable Diffusion API format: inputs is the prompt, parameters are optional
                payload = {
                    "inputs": prompt
                }
                # Add parameters if provided
                if parameters:
                    payload["parameters"] = parameters
                
                print(f"DEBUG [generate_image]: Calling {api_url} with payload: {payload.get('inputs', '')[:50]}...")
                response = requests.post(api_url, headers=headers, json=payload, timeout=120)
                
                if response.status_code == 200:
                    image_bytes = response.content
                    print(f"DEBUG [generate_image]: Direct API call successful, received {len(image_bytes)} bytes")
                elif response.status_code == 503:
                    # Model is loading, wait and retry
                    import time
                    print(f"DEBUG [generate_image]: Model loading (503), waiting 15 seconds...")
                    time.sleep(15)
                    response = requests.post(api_url, headers=headers, json=payload, timeout=120)
                    if response.status_code == 200:
                        image_bytes = response.content
                        print(f"DEBUG [generate_image]: Retry successful, received {len(image_bytes)} bytes")
                    else:
                        error_msg = response.text[:500] if hasattr(response, 'text') else str(response.status_code)
                        raise Exception(f"API returned status {response.status_code} after retry: {error_msg}")
                else:
                    error_msg = response.text[:500] if hasattr(response, 'text') else str(response.status_code)
                    raise Exception(f"API returned status {response.status_code}: {error_msg}")
            
            # Save image to media/images/generated/ directory
            # Use absolute path from project root (where db_path is located)
            db_dir = os.path.dirname(os.path.abspath(self.db_path))
            if not db_dir or db_dir == os.path.dirname(os.path.abspath(__file__)):
                # If db_path is in current directory, use current working directory
                project_root = os.getcwd()
            else:
                project_root = db_dir
            
            media_dir = os.path.join(project_root, "media", "images", "generated")
            os.makedirs(media_dir, exist_ok=True)
            
            print(f"DEBUG [generate_image]: Project root: {project_root}")
            print(f"DEBUG [generate_image]: Saving to directory: {media_dir}")
            print(f"DEBUG [generate_image]: Directory exists: {os.path.exists(media_dir)}")
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Sanitize prompt for filename (first 30 chars, alphanumeric only)
            safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_prompt = safe_prompt.replace(' ', '_')
            filename = f"flux_{timestamp}_{safe_prompt}.png"
            filepath = os.path.join(media_dir, filename)
            
            print(f"DEBUG [generate_image]: Full filepath: {filepath}")
            
            # Save image
            from PIL import Image
            image = Image.open(BytesIO(image_bytes))
            image.save(filepath, "PNG")
            
            print(f"DEBUG [generate_image]: ✅ Image saved successfully to: {filepath}")
            print(f"DEBUG [generate_image]: ✅ Image file exists: {os.path.exists(filepath)}")
            if os.path.exists(filepath):
                print(f"DEBUG [generate_image]: ✅ Image file size: {os.path.getsize(filepath)} bytes")
            else:
                print(f"DEBUG [generate_image]: ❌ ERROR: File was not saved!")
            
            # Log API call
            self._log_api_call(api_name, "text_to_image", "POST", 200, 0)
            
            return filepath
            
        except ImportError:
            print("ERROR [generate_image]: huggingface_hub not installed. Install with: pip install huggingface-hub")
            import traceback
            traceback.print_exc()
            return None
        except Exception as e:
            print(f"ERROR [generate_image]: Exception occurred: {e}")
            import traceback
            traceback.print_exc()
            self._log_api_call(api_name, "text_to_image", "POST", 500, 0)
            return None
    
    # Generic API call method
    def call_api(self, api_name: str, endpoint: str, method: str = "GET",
                 params: Dict = None, data: Dict = None, headers: Dict = None,
                 cache_ttl: int = 300) -> Optional[Dict]:
        """
        Generic method to call any registered API
        
        Args:
            api_name: Name of registered API
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            params: URL parameters
            data: Request body data
            headers: Custom headers
            cache_ttl: Cache TTL in seconds
        
        Returns:
            API response as dict or None
        """
        if api_name not in self.api_configs or not self.api_configs[api_name]['enabled']:
            return None
        
        # Build cache key
        cache_key = f"{api_name}_{endpoint}_{method}_{hash(str(params) + str(data))}"
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached
        
        config = self.api_configs[api_name]['config']
        base_url = config.get('base_url', '')
        
        try:
            start_time = datetime.now()
            
            url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            # Add API key to headers if configured
            request_headers = headers or {}
            if 'api_key' in config:
                request_headers['Authorization'] = f"Bearer {config['api_key']}"
            elif 'api_key_header' in config:
                request_headers[config['api_key_header']] = config['api_key']
            
            if method.upper() == "GET":
                response = requests.get(url, params=params, headers=request_headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, params=params, headers=request_headers, timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, params=params, headers=request_headers, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(url, params=params, headers=request_headers, timeout=10)
            else:
                return None
            
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self._log_api_call(api_name, endpoint, method, response.status_code, response_time)
            
            if response.status_code == 200:
                result = response.json() if response.content else {}
                self._cache_response(cache_key, api_name, result, cache_ttl_seconds=cache_ttl)
                return result
            
            return None
            
        except Exception as e:
            self._log_api_call(api_name, endpoint, method, 500, 0)
            return None
    
    def get_api_status(self) -> Dict:
        """Get status of all registered APIs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT api_name, COUNT(*) as call_count, 
                   AVG(response_time_ms) as avg_response_time,
                   MAX(timestamp) as last_call
            FROM api_call_history
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY api_name
        """)
        
        stats = {}
        for row in cursor.fetchall():
            stats[row[0]] = {
                'call_count': row[1],
                'avg_response_time_ms': row[2] or 0,
                'last_call': row[3]
            }
        
        conn.close()
        
        return {
            'registered_apis': list(self.api_configs.keys()),
            'enabled_apis': [name for name, config in self.api_configs.items() if config['enabled']],
            'statistics': stats
        }
