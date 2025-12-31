#!/usr/bin/env python3
"""
Quick setup script for Google Calendar
Run this to register your Google Calendar
"""

from external_apis import ExternalAPIManager
import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Request both readonly (for reading events) and full access (for adding events)
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar'
]

def setup_google_calendar():
    """Interactive Google Calendar setup"""
    print("📅 Google Calendar Setup")
    print("=" * 50)
    
    # Get database path from config
    db_path = "mo11y_companion.db"
    try:
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config = json.load(f)
                db_path = config.get("db_path", db_path)
    except:
        pass
    
    api = ExternalAPIManager(db_path)
    
    print("\n📝 Google Calendar Setup Instructions")
    print("\n1. Go to Google Cloud Console: https://console.cloud.google.com/")
    print("2. Create a new project (or select existing)")
    print("3. Enable Google Calendar API:")
    print("   - Go to 'APIs & Services' > 'Library'")
    print("   - Search for 'Google Calendar API'")
    print("   - Click 'Enable'")
    print("4. Create OAuth 2.0 credentials:")
    print("   - Go to 'APIs & Services' > 'Credentials'")
    print("   - Click 'Create Credentials' > 'OAuth client ID'")
    print("   - Application type: 'Desktop app'")
    print("   - Name it (e.g., 'Mo11y Calendar')")
    print("   - Click 'Create'")
    print("   - Download the JSON file")
    print("5. Save the downloaded file as 'credentials.json' in this directory")
    print("\n" + "=" * 50)
    
    # Check for credentials file
    credentials_path = "credentials.json"
    if not os.path.exists(credentials_path):
        print(f"\n❌ Credentials file not found at {credentials_path}")
        print("Please download your OAuth2 credentials from Google Cloud Console")
        print("and save it as 'credentials.json' in this directory.")
        return False
    
    print(f"\n✅ Found credentials file: {credentials_path}")
    
    # Try to list available calendars
    print("\n📋 Fetching your available calendars...")
    try:
        creds_temp = None
        token_path_temp = "token.json"
        if os.path.exists(token_path_temp):
            try:
                creds_temp = Credentials.from_authorized_user_file(token_path_temp, SCOPES)
            except:
                pass
        
        if not creds_temp or not creds_temp.valid:
            if creds_temp and creds_temp.expired and creds_temp.refresh_token:
                try:
                    creds_temp.refresh(Request())
                except:
                    creds_temp = None
        
        if creds_temp and creds_temp.valid:
            try:
                service = build('calendar', 'v3', credentials=creds_temp)
                calendar_list = service.calendarList().list().execute()
                calendars = calendar_list.get('items', [])
                
                if calendars:
                    print("\n📅 Available calendars:")
                    for i, cal in enumerate(calendars, 1):
                        cal_id = cal.get('id', 'unknown')
                        cal_summary = cal.get('summary', 'No name')
                        cal_primary = " (PRIMARY)" if cal.get('primary', False) else ""
                        print(f"   {i}. {cal_summary} - ID: '{cal_id}'{cal_primary}")
                    
                    print("\n💡 Tip: Use 'primary' for your main calendar, or copy the ID from above")
                else:
                    print("   No calendars found (this is unusual)")
            except Exception as e:
                print(f"   Could not list calendars: {e}")
        else:
            print("   Need to authenticate first to list calendars")
    except Exception as e:
        print(f"   Could not list calendars: {e}")
    
    # Ask for calendar ID (default to primary)
    print("\n" + "=" * 50)
    calendar_id = input("\nEnter calendar ID (or press Enter for 'primary'): ").strip()
    if not calendar_id:
        calendar_id = "primary"
    
    # Authenticate and get token
    print("\n⏳ Authenticating with Google...")
    creds = None
    
    # Load existing token if available
    token_path = "token.json"
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            error_str = str(e)
            if 'invalid_scope' in error_str or 'Bad Request' in error_str:
                print(f"⚠️  Token scope mismatch detected!")
                print(f"   The existing token was created with different scopes.")
                print(f"   Deleting old token and creating a new one...")
                try:
                    os.remove(token_path)
                    print(f"   ✅ Old token deleted")
                except:
                    print(f"   ⚠️  Could not delete token automatically. Please delete {token_path} manually.")
                creds = None
            else:
                print(f"⚠️  Error loading existing token: {e}")
                print("Will create new token...")
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"❌ Error refreshing token: {e}")
                print("Will need to re-authenticate...")
                creds = None
        
        if not creds:
            print("\n🌐 Opening browser for authentication...")
            print("Please authorize Mo11y to access your Google Calendar")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print(f"✅ Token saved to {token_path}")
    
    # Test connection by getting calendar info
    try:
        service = build('calendar', 'v3', credentials=creds)
        calendar = service.calendars().get(calendarId=calendar_id).execute()
        print(f"\n✅ Successfully connected to calendar: {calendar.get('summary', calendar_id)}")
    except Exception as e:
        print(f"\n⚠️  Warning: Could not verify calendar access: {e}")
        print("Continuing anyway...")
    
    # Register with ExternalAPIManager
    print(f"\n⏳ Registering Google Calendar...")
    api.register_google_calendar(
        credentials_path=credentials_path,
        token_path=token_path,
        calendar_id=calendar_id
    )
    
    print("✅ Google Calendar registered successfully!")
    
    # Test it
    print(f"\n🧪 Testing Google Calendar connection...")
    events = api.get_calendar_events(days_ahead=7)
    
    if events is not None:
        print(f"\n✅ Google Calendar connection successful!")
        print(f"   Found {len(events)} events in the next 7 days")
        
        if events:
            print("\n📋 Upcoming events:")
            for event in events[:5]:  # Show first 5
                title = event.get('title', 'No title')
                start = event.get('start', 'Unknown')
                print(f"   - {title} ({start})")
        else:
            print("   No events found in the next 7 days")
        
        print("\n🎉 You can now ask Mo11y about your calendar!")
        return True
    else:
        print("\n⚠️  Google Calendar registered but test failed.")
        print("   Check your credentials and calendar ID.")
        return False

if __name__ == "__main__":
    setup_google_calendar()
