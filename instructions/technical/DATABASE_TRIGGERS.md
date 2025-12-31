# Database Storage Triggers Guide

## Overview

Mo11y uses **three storage systems**:

1. **EnhancedMemory** (SPOHNZ.db) - SQLite database
2. **LifeJournal** (life-journal.json) - JSON file  
3. **ExternalAPIManager** (tables in SPOHNZ.db) - API configs and cache

## 1. EnhancedMemory (SPOHNZ.db)

### What Gets Saved:
- **Episodic Memories**: Every conversation/interaction
- **Semantic Memories**: Facts about you (preferences, traits)
- **Emotional Memories**: When sentiment is significant (> 0.3)
- **Relationship Milestones**: Important relationship events
- **User Preferences**: Explicit preferences you set
- **Media Memories**: Images/files you share

### How to Trigger Saves:

#### Episodic Memory (Every Conversation)
**Automatic** - Happens in every agent interaction:
```
You: "Hello, how are you?"
Agent: [responds]
→ Saves: "User: Hello, how are you?\nAssistant: [response]"
```

#### Semantic Memory (Facts About You)
**Trigger phrases**:
- "I am..." or "I'm..."
- "I like..."
- "I have..."
- "I work at..."
- "My favorite..."

**Example**:
```
You: "I am a software engineer"
→ Saves semantic memory: "user_trait: software engineer"
```

**Test it**:
```python
# In agent conversation:
"I am a Python developer"
"I like hiking and reading"
"My favorite color is blue"
```

#### Emotional Memory (Sentiment)
**Automatic** - Triggers when sentiment > 0.3 (positive or negative)

**Example**:
```
You: "I'm so happy today!" (high positive sentiment)
→ Saves emotional memory: emotion_type="positive", intensity=0.7
```

**Test it**:
```python
# High positive sentiment:
"I'm thrilled!"
"I love this!"
"Amazing!"

# High negative sentiment:
"I'm frustrated"
"This is terrible"
"I hate when..."
```

## 2. LifeJournal (life-journal.json)

### What Gets Saved:
- **Timeline Entries**: Events with dates/years
- **Friends**: People you mention
- **Locations**: Places you've been
- **Education**: Schools/universities
- **Career**: Employers/jobs
- **Relationships**: Personal relationships

### When It Saves:
**Only active when using Alex Mercer or CJS persona**

### How to Trigger Saves:

#### Timeline Entry
**Trigger**: Mention dates, years, or time periods

**Example**:
```
You: "In 2020, I moved to Texas"
→ Saves timeline entry: year=2020, content="moved to Texas"
```

**Test it**:
```python
"In 2015, I graduated from college"
"Last year, I started a new job"
"Back in 2010, I lived in California"
```

#### Friends
**Trigger**: Mention names of people

**Example**:
```
You: "I met John at work"
→ Saves friend: name="John", met_at="work"
```

**Test it**:
```python
"I had lunch with Sarah yesterday"
"My friend Mike is coming to visit"
"I met Alice at the conference"
```

**Note**: Requires spaCy NLP library for best results. Without it, uses simple heuristics.

#### Locations
**Trigger**: Mention cities, states, addresses

**Example**:
```
You: "I lived in Dallas, Texas for 5 years"
→ Saves location: city="Dallas", state="TX"
```

**Test it**:
```python
"I moved to Austin, Texas"
"I visited New York last month"
"I grew up in California"
```

## 3. ExternalAPIManager (API Tables in SPOHNZ.db)

### What Gets Saved:
- **API Configurations**: When APIs are registered
- **API Cache**: Cached API responses
- **API Call History**: Logs of API calls

### How to Trigger Saves:

#### API Registration
**Trigger**: When external APIs are set up

**Example**:
```python
# Via setup scripts:
python3 setup_weather.py
python3 setup_caldav.py
```

#### API Cache
**Trigger**: When APIs return responses (weather, calendar, etc.)

**Example**:
```
You: "What's the weather?"
→ Agent calls weather API
→ Saves cached response in api_cache table
```

## Testing All Systems

Run the test script:
```bash
python3 test_databases.py
```

This will:
1. ✅ Test EnhancedMemory (episodic, semantic, emotional)
2. ✅ Test LifeJournal (timeline, friends, locations)
3. ✅ Test ExternalAPIManager (API registration)

## Quick Test Commands

### Test Episodic Memory (Every Conversation)
Just chat with the agent - every message saves automatically.

### Test Semantic Memory
```
"I am a software engineer"
"I like Python programming"
"My favorite food is pizza"
```

### Test Emotional Memory
```
"I'm so excited!" (positive)
"I'm really frustrated" (negative)
```

### Test LifeJournal (Alex Mercer/CJS persona)
```
"In 2020, I moved to Texas"
"I met John at work"
"I lived in Dallas for 5 years"
```

## Troubleshooting

### Nothing Saving to EnhancedMemory?
- Check: Is agent running? (`store_memory` function called?)
- Check: Database path correct in config.json?
- Check: Database file writable?

### Nothing Saving to LifeJournal?
- Check: Are you using Alex Mercer or CJS persona?
- Check: Is `life_journal` initialized in agent?
- Check: Journal file path correct?

### Nothing Saving to ExternalAPIManager?
- Check: Are external APIs enabled?
- Check: Are APIs actually being called?
- Check: API setup scripts run?

## Verification

Check database contents:
```bash
sqlite3 SPOHNZ.db "SELECT COUNT(*) FROM episodic_memories;"
sqlite3 SPOHNZ.db "SELECT COUNT(*) FROM semantic_memories;"
sqlite3 SPOHNZ.db "SELECT COUNT(*) FROM emotional_memories;"
```

Check journal file:
```bash
cat life-journal.json | jq '.timeline | length'
cat life-journal.json | jq '.friends | length'
```
