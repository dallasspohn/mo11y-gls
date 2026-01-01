# How to Set Preferences Count to 1 (or Any Number)

Based on grepping the codebase, here are **all the ways** to set preferences:

## Method 1: Using the Python Script (Easiest)

I've created `set_preference.py` for you:

```bash
python3 set_preference.py
```

This will add one preference and set the count to 1.

## Method 2: Direct Python Code

```python
from enhanced_memory import EnhancedMemory

memory = EnhancedMemory("/home/dallas/dev/mo11y/SPOHNZ.db")

# Add a preference
memory.update_preference(
    category="general",  # or "food", "hobbies", "music", etc.
    key="your_preference_key",
    value="your preference value",
    confidence=1.0
)
```

## Method 3: Direct SQL (Quick & Dirty)

```bash
sqlite3 /home/dallas/dev/mo11y/SPOHNZ.db <<EOF
INSERT OR REPLACE INTO user_preferences 
(category, preference_key, preference_value, confidence, last_updated)
VALUES ('general', 'test', 'This is a test preference', 1.0, CURRENT_TIMESTAMP);
EOF
```

## Method 4: Through Conversation (Automatic)

The agent automatically learns preferences when you say:
- **"I like [something]"** → Extracted as `user_preference` semantic memory
- **"I am [something]"** → Extracted as `user_trait` semantic memory

**However**, these go into `semantic_memories` table, NOT `user_preferences` table!

The count shown in the UI comes from `user_preferences` table only.

## Method 5: Delete All and Add One

If you have too many preferences and want to reset to 1:

```bash
sqlite3 /home/dallas/dev/mo11y/SPOHNZ.db <<EOF
DELETE FROM user_preferences;
INSERT INTO user_preferences 
(category, preference_key, preference_value, confidence, last_updated)
VALUES ('general', 'single_preference', 'My one preference', 1.0, CURRENT_TIMESTAMP);
EOF
```

## Understanding the Difference

### `user_preferences` table (what the count shows):
- Used by: `memory.update_preference()`
- Displayed in: Sidebar "Preferences Learned" metric
- Structure: `(category, preference_key, preference_value, confidence)`

### `semantic_memories` table (learned from conversation):
- Used by: Agent when you say "I like..."
- Stored as: `user_preference_{hash}` keys
- NOT counted in "Preferences Learned"

## Current Status

Your database currently has:
- **0 preferences** in `user_preferences` table
- The script I ran added 1 preference, so count should now be **1**

## Verify Your Count

```bash
sqlite3 /home/dallas/dev/mo11y/SPOHNZ.db "SELECT COUNT(*) FROM user_preferences;"
```

## See All Preferences

```bash
sqlite3 /home/dallas/dev/mo11y/SPOHNZ.db "SELECT category, preference_key, preference_value FROM user_preferences;"
```

## Code Locations

- **Preference storage**: `enhanced_memory.py` line 231 (`update_preference()`)
- **Preference count**: `enhanced_memory.py` line 437 (`get_relationship_summary()`)
- **Display**: `app_enhanced.py` line 294 (`st.metric("Preferences Learned")`)
