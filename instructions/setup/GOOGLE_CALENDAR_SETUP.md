# Google Calendar Setup Guide

This guide will help you set up Google Calendar integration with Mo11y.

## Prerequisites

1. A Google account
2. Access to Google Cloud Console

## Step 1: Enable Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the Google Calendar API:
   - Navigate to **APIs & Services** > **Library**
   - Search for "Google Calendar API"
   - Click **Enable**

## Step 2: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - Choose **External** (unless you have a Google Workspace account)
   - Fill in the required information
   - Add your email to test users
   - Save and continue
4. Create OAuth client ID:
   - Application type: **Desktop app**
   - Name: `Mo11y Calendar` (or any name you prefer)
   - Click **Create**
5. Download the credentials JSON file
6. Save it as `credentials.json` in the Mo11y project directory

## Step 3: Run Setup Script

Run the setup script:

```bash
python3 setup_google_calendar.py
```

The script will:
1. Check for `credentials.json`
2. Open your browser for authentication
3. Ask you to authorize Mo11y to access your Google Calendar
4. Save the authentication token
5. Test the connection

## Step 4: Verify Setup

After setup, you can test the integration by asking Mo11y about your calendar:

- "What's on my calendar this week?"
- "Show me my upcoming events"
- "Add a meeting tomorrow at 2pm"

## Troubleshooting

### "Credentials file not found"
- Make sure `credentials.json` is in the project root directory
- Check that you downloaded the correct file from Google Cloud Console

### "Token expired or invalid"
- Run `python3 setup_google_calendar.py` again to re-authenticate
- The token will be refreshed automatically

### "Calendar not found"
- Make sure you're using the correct calendar ID
- Use `primary` for your main calendar
- For other calendars, find the calendar ID in Google Calendar settings

### Calendar ID for Non-Primary Calendars

To use a calendar other than your primary calendar:

1. Go to [Google Calendar](https://calendar.google.com/)
2. Click the three dots next to the calendar name
3. Select **Settings and sharing**
4. Scroll down to **Integrate calendar**
5. Copy the **Calendar ID** (it looks like an email address)
6. Use this ID when running the setup script

## Security Notes

- `credentials.json` contains your OAuth client credentials (safe to keep)
- `token.json` contains your access token (keep secure, don't share)
- Both files are stored locally and never sent to external servers
- Tokens automatically refresh when they expire

## Features

Once set up, Mo11y can:
- ✅ View your upcoming calendar events
- ✅ Add new events to your calendar
- ✅ Delete events from your calendar
- ✅ Answer questions about your schedule
