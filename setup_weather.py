#!/usr/bin/env python3
"""
Quick setup script for Weather API
Run this to register your weather API key
"""

from external_apis import ExternalAPIManager
import json
import os

def setup_weather():
    """Interactive weather API setup"""
    print("🌤️  Weather API Setup")
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
    
    # Convert to absolute path if relative
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(db_path)
    
    print(f"Using database: {db_path}")
    
    api = ExternalAPIManager(db_path)
    
    print("\nChoose a weather provider:")
    print("1. OpenWeatherMap (recommended)")
    print("2. WeatherAPI.com")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        provider = "openweathermap"
        print("\n📝 Get your API key from: https://openweathermap.org/api")
        print("   (Free tier: 60 calls/minute)")
    elif choice == "2":
        provider = "weather_api"
        print("\n📝 Get your API key from: https://www.weatherapi.com/")
        print("   (Free tier: 1M calls/month)")
    else:
        print("Invalid choice. Using OpenWeatherMap.")
        provider = "openweathermap"
    
    api_key = input("\nEnter your API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Exiting.")
        return False
    
    location = input("Enter default location (or press Enter for 'Crandall, TX'): ").strip()
    if not location:
        location = "Crandall, TX"
    
    print(f"\n⏳ Registering Weather API...")
    api.register_weather_api(
        api_key=api_key,
        provider=provider,
        default_location=location
    )
    
    print("✅ Weather API registered successfully!")
    
    # Test it
    print(f"\n🧪 Testing weather API for {location}...")
    weather = api.get_weather()
    
    if weather:
        print("\n✅ Weather API is working!")
        print(f"   Location: {weather.get('location', 'Unknown')}")
        print(f"   Temperature: {weather.get('temperature', 'N/A')}°F")
        print(f"   Conditions: {weather.get('description', 'N/A').title()}")
        print("\n🎉 You can now ask Mo11y about the weather!")
        return True
    else:
        print("\n⚠️  Weather API registered but test failed.")
        print("   Check your API key and try again.")
        return False

if __name__ == "__main__":
    setup_weather()
