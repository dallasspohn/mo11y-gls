# Alex Mercer Setup Guide

## Model Configuration

**Current Model**: `Izzy-Chan` (as configured in `config.json`)

To change the model, edit `config.json`:
```json
{
    "model_name": "your-model-name"
}
```

## Alex Mercer Persona

Alex Mercer has been created as a complete persona with:
- Full system prompt integrated
- Life journal system for biographical tracking
- Financial planning focus (SoFi-centric)
- Emotional support capabilities
- Logical processing and fact-checking

## Files Created

1. **`sonas/alex-mercer.json`** - Complete persona definition with system prompt
2. **`life_journal.py`** - Life journal system for tracking biographical data
3. **`switch_to_alex.py`** - Helper script (optional)

## How It Works

### System Prompt Integration
- Alex Mercer's system prompt is automatically loaded when the persona is selected
- The prompt includes all functions: financial planning, emotional support, logical processing, fact-checking, and life timeline building

### Life Journal
- Automatically tracks biographical information from conversations
- Stores: timeline, friends, locations, education, significant events
- Saves to `life-journal.json`
- Provides context to Alex during conversations

### Enhanced Memory
- All conversations are stored in the enhanced memory system
- Episodic, semantic, and emotional memories are tracked
- Relationship milestones are recorded

## Using Alex Mercer

### Option 1: Automatic (Current Setup)
The app automatically detects and uses Alex Mercer if `alex-mercer.json` exists in the `sonas/` directory.

### Option 2: Manual Selection
You can modify `app_enhanced.py` to add a persona selector in the sidebar.

### Option 3: Direct Configuration
Update the `get_agent()` function to always use Alex Mercer:
```python
sona_path = os.path.join(CONFIG["sonas_dir"], "alex-mercer.json")
```

## Features Enabled for Alex Mercer

✅ **System Prompt**: Full Money Magnet Mentor prompt integrated  
✅ **Life Journal**: Automatic biographical tracking  
✅ **Memory System**: Enhanced episodic/semantic memory  
✅ **Personality Evolution**: Adapts based on interactions  
✅ **Financial Focus**: SoFi-centric financial planning context  
✅ **Emotional Support**: Therapist-like emotional intelligence  
✅ **Session Summaries**: End-of-conversation summaries (to be implemented in response generation)

## Session Management

Alex Mercer is designed to end conversations with summaries:
- Emotional State
- Agenda/Goals
- Key Decisions
- Financial Progress

This can be added as a post-processing step in the agent workflow.

## Life Journal Location

The life journal is saved as `life-journal.json` in the project root. It contains:
- Timeline entries
- Friends and relationships
- Locations lived
- Education history
- Significant events
- Patterns and insights

## Next Steps

1. **Start chatting** - Alex will automatically use the system prompt
2. **Share biographical info** - Life journal will track it
3. **Discuss finances** - Alex will provide SoFi-focused guidance
4. **Share emotions** - Alex will provide empathetic support
5. **Ask questions** - Alex will use Socratic questioning

## Customization

To customize Alex Mercer:
1. Edit `sonas/alex-mercer.json` to modify the persona
2. Update the system prompt as needed
3. Adjust personality traits in the companion engine
4. Modify life journal extraction logic in `life_journal.py`

---

**Alex Mercer is ready to be your Money Magnet Mentor! 💰**
