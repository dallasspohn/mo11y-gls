# Model Switching & Memory Persistence Guide

## How Model Switching Works

### 1. "Get Available Models" and "Model Found" Steps

These are **validation steps** in the LangGraph flow that happen **every time you send a message**:

1. **Get Available Models**: The system calls `ollama list` to get all available models from your Ollama installation
2. **Model Found?**: It checks if the specified model (from `config.json` or sona file) exists in that list
3. If **not found**: Shows an error with available models and suggests pulling the model
4. If **found**: Proceeds with using that model

This ensures the model exists before trying to use it, preventing runtime errors.

### 2. Per-Sona Model Switching

**YES, this feature works!** You can configure different models for different sonas.

#### How It Works:

1. The system first checks `config.json` for the default `model_name`
2. When a sona is selected, it checks if that sona's JSON file has a `model_name` field
3. If the sona has `model_name`, it uses that model instead of the default
4. If not, it falls back to the default from `config.json`

#### How to Configure:

Add a `model_name` field to any sona JSON file:

```json
{
    "name": "Izzy-Chan",
    "model_name": "llama3.2:3b",
    "description": "...",
    ...
}
```

**Example**: You could have:
- **Mo11y** → Uses `deepseek-r1:latest` (from config.json)
- **Izzy-Chan** → Uses `llama3.2:3b` (from sona file)
- **Alex Mercer** → Uses `phi3:mini` (from sona file)

The model switches automatically when you change personas in the sidebar!

## Memory Persistence Issue

### The Problem

Your memories are being reset to "Total Interaction: 1" every time you restart Streamlit.

### Root Cause

The database path should be consistent (`/home/dallas/mo11y/SPOHNZ.db` from your `config.json`), but there might be:
1. Streamlit cache issues causing agent recreation
2. Database path resolution problems
3. Multiple database files being created

### The Fix

I've updated the code to:
1. **Always use absolute paths** for the database
2. **Print the database path** being used (check console output)
3. **Ensure consistency** across all agent creations

### Verify Your Database

Check your database:
```bash
sqlite3 /home/dallas/dev/mo11y/SPOHNZ.db "SELECT COUNT(*) FROM episodic_memories;"
```

If it shows more than 1 interaction but the UI shows 1, there's a path mismatch issue.

### Troubleshooting

1. **Check config.json**: Ensure `db_path` is set correctly:
   ```json
   {
       "db_path": "/home/dallas/mo11y/SPOHNZ.db"
   }
   ```

2. **Check console output**: When Streamlit starts, you should see:
   ```
   Using database: /home/dallas/mo11y/SPOHNZ.db
   ```

3. **Verify database exists**: 
   ```bash
   ls -lh /home/dallas/dev/mo11y/SPOHNZ.db
   ```

4. **Check for multiple databases**: 
   ```bash
   find /home/dallas/dev/mo11y -name "*.db" -type f
   ```

## Quick Setup for Per-Sona Models

1. **List your available models**:
   ```bash
   ollama list
   ```

2. **Edit a sona file** (e.g., `sonas/izzy.json`):
   ```json
   {
       "name": "Izzy-Chan",
       "model_name": "llama3.2:3b",  // Add this line
       "description": "...",
       ...
   }
   ```

3. **Restart Streamlit** - the model will switch automatically when you select that persona!

## Notes

- The model validation happens **every message** to ensure the model is still available
- All sonas share the **same database** (`SPOHNZ.db`) - memories persist across persona switches
- If a sona doesn't have `model_name`, it uses the default from `config.json`
- The database path is now always resolved to an absolute path to prevent issues
