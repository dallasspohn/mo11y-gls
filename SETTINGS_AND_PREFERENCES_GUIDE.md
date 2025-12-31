# Settings and Preferences Guide

## 1. Personality Configuration

### Current State
The personality traits in Settings are **auto-adjusted** based on your interactions. They start at default values and evolve over time:

**Default Values:**
- Warmth: 0.7
- Playfulness: 0.6
- Empathy: 0.8
- Directness: 0.5
- Humor: 0.6
- Proactivity: 0.5
- Supportiveness: 0.8
- Curiosity: 0.7

### Why They're All High
If you see all traits at the high end (0.8-1.0), it means:
- The personality has evolved upward based on positive interactions
- Traits increase by small amounts (0.01-0.02) per interaction
- After many conversations, they naturally drift higher

### Can You Change Them?
**No** - The sliders are disabled because traits are meant to evolve organically. However, you can:

1. **Reset to defaults** (if you want to start fresh):
```python
from enhanced_memory import EnhancedMemory
import sqlite3

db_path = "./SPOHNZ.db"  # or from config.json
memory = EnhancedMemory(db_path)

# Reset personality traits to defaults
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

default_traits = {
    'warmth': 0.7,
    'playfulness': 0.6,
    'empathy': 0.8,
    'directness': 0.5,
    'humor': 0.6,
    'proactivity': 0.5,
    'supportiveness': 0.8,
    'curiosity': 0.7
}

for trait, value in default_traits.items():
    cursor.execute("""
        UPDATE personality_traits
        SET current_value = ?, trend = 0.0
        WHERE trait_name = ?
    """, (value, trait))

conn.commit()
conn.close()
print("✓ Personality traits reset to defaults")
```

2. **Manually set specific values**:
```python
# Set warmth to 0.5
cursor.execute("""
    UPDATE personality_traits
    SET current_value = 0.5, trend = 0.0
    WHERE trait_name = 'warmth'
""")
conn.commit()
```

## 2. Relationship Milestones

### Two Milestone Systems

There are **TWO separate milestone systems**:

#### System 1: Database Milestones (SPOHNZ.db)
- **Location**: `relationship_milestones` table in the database
- **Display**: Shown in Streamlit app → Relationship page → "💝 Relationship Milestones"
- **Managed by**: `enhanced_memory.py` → `add_milestone()` method
- **Automatic creation**: ✅ Now enabled (see below)

#### System 2: Persona JSON Milestones (alex-mercer.json)
- **Location**: `relationship_evolution.relationship_milestones` in persona JSON files
- **Display**: Used by the persona for context (not shown in UI)
- **Managed by**: `AlexConversationUpdater` / `CJSConversationUpdater`
- **Automatic creation**: ✅ Already working
  - Creates milestones at: 1st, 10th, 20th conversations
  - Stored in: `sonas/alex-mercer.json` or `sonas/cjs.json`

### When Do Database Milestones Show Up?
Database milestones are now **automatically created** and appear in:
- **Relationship page** → "💝 Relationship Milestones" section
- **Relationship page** → "🎯 Milestone Timeline" chart

### Adding Milestones Manually

**Method 1: Using Python Script**
```python
from enhanced_memory import EnhancedMemory

memory = EnhancedMemory("./SPOHNZ.db")

# Add a milestone
memory.add_milestone(
    milestone_type="first_conversation",
    description="Our first conversation together",
    significance=0.9
)

# Add milestone for 100th interaction
memory.add_milestone(
    milestone_type="milestone_interaction",
    description="100th conversation milestone",
    significance=0.8
)
```

**Method 2: Direct SQL**
```bash
sqlite3 SPOHNZ.db <<EOF
INSERT INTO relationship_milestones 
(milestone_type, description, significance)
VALUES 
('first_conversation', 'Our first conversation', 0.9),
('milestone_interaction', '100th conversation', 0.8),
('personal_sharing', 'First time sharing personal story', 0.7);
EOF
```

**Method 3: Check Your Current Milestones**
```bash
sqlite3 SPOHNZ.db "SELECT milestone_type, description, timestamp FROM relationship_milestones ORDER BY timestamp DESC;"
```

### Automatic Milestone Creation ✅

#### Database Milestones (SPOHNZ.db)
Created automatically in the database for:
- **First conversation** - When you have your first chat
- **Interaction milestones** - At 10th, 25th, 50th, 100th, 250th, 500th, 1000th conversations
- **First personal sharing** - When you first share personal information ("I'm...", "I feel...", etc.)
- **First preference learned** - When the first preference is recorded
- **Significant emotional moments** - When sentiment is very high (>0.7 or <-0.7)

#### Persona JSON Milestones (alex-mercer.json / cjs.json)
Created automatically in the persona JSON files for:
- **1st conversation** - "First conversation"
- **10th conversation** - "10th conversation - relationship deepening"
- **20th conversation** - "20th conversation - strong connection established"

**Note**: These are separate systems! Database milestones show in the UI, while JSON milestones are used by the persona for context.

## 3. Adding Preferences

### What Are Preferences?
Preferences are things the AI learns about you (likes, dislikes, habits, etc.). They're separate from semantic memories and are counted in the "Preferences Learned" metric.

### How to Add Preferences

**Method 1: Using the Script (Easiest)**
```bash
python3 set_preference.py
```

**Method 2: Using Python Code**
```python
from enhanced_memory import EnhancedMemory

memory = EnhancedMemory("./SPOHNZ.db")

# Add preferences by category
memory.update_preference(
    category="food",
    key="favorite_coffee",
    value="Dark roast with cream",
    confidence=1.0
)

memory.update_preference(
    category="hobbies",
    key="weekend_activity",
    value="Hiking and reading",
    confidence=0.9
)

memory.update_preference(
    category="music",
    key="favorite_genre",
    value="Grunge and alternative rock",
    confidence=1.0
)

memory.update_preference(
    category="work",
    key="preferred_meeting_time",
    value="Morning meetings before 11am",
    confidence=0.8
)
```

**Method 3: Direct SQL**
```bash
sqlite3 SPOHNZ.db <<EOF
INSERT OR REPLACE INTO user_preferences 
(category, preference_key, preference_value, confidence, last_updated)
VALUES 
('food', 'favorite_coffee', 'Dark roast with cream', 1.0, CURRENT_TIMESTAMP),
('hobbies', 'weekend_activity', 'Hiking and reading', 0.9, CURRENT_TIMESTAMP),
('music', 'favorite_genre', 'Grunge and alternative rock', 1.0, CURRENT_TIMESTAMP);
EOF
```

### Preference Categories
Common categories include:
- `general` - General preferences
- `food` - Food and drink preferences
- `hobbies` - Hobbies and interests
- `music` - Music preferences
- `movies` - Movie/TV preferences
- `work` - Work-related preferences
- `lifestyle` - Lifestyle choices
- `communication` - Communication style preferences

### Viewing Your Preferences
```bash
# Count preferences
sqlite3 SPOHNZ.db "SELECT COUNT(*) FROM user_preferences;"

# List all preferences
sqlite3 SPOHNZ.db "SELECT category, preference_key, preference_value FROM user_preferences;"

# By category
sqlite3 SPOHNZ.db "SELECT * FROM user_preferences WHERE category = 'food';"
```

### Preferences vs Semantic Memories
- **Preferences** (`user_preferences` table): Explicit preferences you set
- **Semantic Memories** (`semantic_memories` table): Facts learned from conversation (e.g., "I like coffee" → stored as semantic memory)

The "Preferences Learned" count only includes `user_preferences` table entries.

## Quick Reference

### Check Current State
```python
from enhanced_memory import EnhancedMemory

memory = EnhancedMemory("./SPOHNZ.db")
summary = memory.get_relationship_summary()

print(f"Total Interactions: {summary['total_interactions']}")
print(f"Preferences Learned: {summary['preferences_learned']}")
print(f"Milestones: {len(summary['milestones'])}")
```

### Reset Everything (if needed)
```python
# Reset personality traits
# Reset preferences (delete all)
# Reset milestones (delete all)
# See reset script examples above
```

## Troubleshooting

**Q: Why are personality traits all at 1.0?**
A: They've evolved upward over many interactions. This is normal! You can reset them if desired.

**Q: Why don't I see any milestones?**
A: Milestones aren't automatically created yet. Add them manually using the methods above.

**Q: How do I know if preferences are being saved?**
A: Check the "Preferences Learned" metric in the Relationship page, or query the database directly.

**Q: Can I edit preferences after adding them?**
A: Yes! Use `update_preference()` with the same category/key - it will update the value.
