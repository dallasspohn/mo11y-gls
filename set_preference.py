#!/usr/bin/env python3
"""
Simple script to add a preference to the database
This will set the preference count to 1 (or add one if it's 0)
"""

import json
import os
from enhanced_memory import EnhancedMemory

# Get database path from config.json
db_path = "/home/dallas/dev/mo11y/SPOHNZ.db"
if os.path.exists("config.json"):
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            db_path = config.get("db_path", db_path)
    except:
        pass

# Convert to absolute path if relative
if not os.path.isabs(db_path):
    db_path = os.path.abspath(db_path)

print(f"Using database: {db_path}")

# Initialize memory system
memory = EnhancedMemory(db_path)

# Add a preference
# Format: category, key, value
# Example categories: "food", "hobbies", "music", "movies", "lifestyle", etc.

# Option 1: Add a simple preference
memory.update_preference(
    category="general",
    key="test_preference",
    value="This is a test preference to set count to 1",
    confidence=1.0
)

print("✓ Preference added successfully!")
print(f"  Category: general")
print(f"  Key: test_preference")
print(f"  Value: This is a test preference to set count to 1")

# Verify the count
summary = memory.get_relationship_summary()
print(f"\n✓ Preference count is now: {summary['preferences_learned']}")

# Show all preferences
all_prefs = memory.get_all_preferences()
if all_prefs:
    print("\nAll preferences:")
    for category, prefs in all_prefs.items():
        print(f"  {category}:")
        for key, data in prefs.items():
            print(f"    - {key}: {data['value']}")
