# Quick Weather Setup

## Problem

Alex Mercer isn't answering weather questions because the weather API isn't configured.

## Quick Fix

Run the setup script:

```bash
python3 setup_weather.py
```

This will:
1. Ask which weather service you want (OpenWeatherMap or WeatherAPI.com)
2. Prompt for your API key
3. Register it automatically

## Get Free API Keys

### Option 1: OpenWeatherMap (Recommended)
1. Go to: https://openweathermap.org/api
2. Sign up (free)
3. Get your API key from the dashboard
4. Run `python3 setup_weather.py` and enter the key

### Option 2: WeatherAPI.com
1. Go to: https://www.weatherapi.com/
2. Sign up (free tier available)
3. Get your API key
4. Run `python3 setup_weather.py` and enter the key

## After Setup

Once configured, Alex Mercer will be able to answer:
- "What's the weather like?"
- "What will the weather be tomorrow morning?"
- "Is it going to rain today?"
- "What's the temperature in Crandall, TX?"

## Fallback: Web Search

If weather API isn't configured, the agent will automatically use web search to find weather information when you ask weather questions.

## Test It

After setup, ask:
```
"What's the weather like tomorrow morning?"
```

Alex Mercer should now provide weather information!
