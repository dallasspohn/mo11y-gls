# Mo11y Personal Data Backup Guide

## Critical Personal Data Files

These files contain your personal data, memories, conversations, and configurations. **Back these up regularly!**

### 1. **Databases** (Most Important!)
Contains all your memories, personality evolution, preferences, calendar events, tasks, and reminders.

- `mo11y_companion.db` - Main database (memories, personality, preferences)
- `SPOHNZ.db` - Alternative database path (check config.json to see which is active)
- `test_*.db` - Test databases (optional, can skip)

**Location**: Root directory (`/home/dallas/mo11y/`)

### 2. **Life Journal**
Personal biographical data tracked over time.

- `life-journal.json` - Your life journal entries

**Location**: Root directory (`/home/dallas/mo11y/`)

### 3. **Persona Files (SONAs)**
Your custom persona configurations.

- `sonas/alex-mercer.json` - Alex Mercer persona
- `sonas/cjs.json` - CJS persona  
- `sonas/izzy.json` - Izzy persona
- `sonas/tool-builder.json` - Tool Builder persona
- `sonas/*.json` - Any other persona files
- `sonas/*.backup` - Backup copies (optional but good to keep)

**Location**: `sonas/` directory

### 4. **RAG Files**
Knowledge bases and biographical data.

- `RAGs/cjs.json` - CJS knowledge base
- `RAGs/Clark_rag.json` - Clark knowledge base
- `RAGs/dallas.json` - Your personal knowledge base
- `RAGs/*.json` - All other RAG files

**Location**: `RAGs/` directory

### 5. **Conversation Logs**
Detailed logs of all conversations (useful for debugging and review).

- `conversation_logs/*.txt` - Full conversation logs
- `conversation_logs/*_summary.txt` - Summary logs (last 30 exchanges)

**Location**: `conversation_logs/` directory

### 6. **Configuration File**
Your personal settings and API keys.

- `config.json` - Main configuration (contains Telegram tokens, model settings, etc.)

**⚠️ Security Note**: Contains API keys/tokens. Store securely!

**Location**: Root directory (`/home/dallas/mo11y/`)

### 7. **OAuth Tokens** (If using Google Calendar)
Google Calendar authentication token.

- `token.json` - Google OAuth token (if using Google Calendar integration)

**⚠️ Security Note**: Contains authentication credentials. Store securely!

**Location**: Root directory (`/home/dallas/mo11y/`)

### 8. **Media Files** (Optional but Recommended)
Uploaded images, audio files, and other media associated with memories.

- `media/` - Directory containing uploaded media files

**Location**: `media/` directory

### 9. **Custom Modelfiles** (If you have any)
Custom Ollama model configurations.

- `Modelfile.jim` - Custom modelfile (if you created one)
- `Modelfile.*` - Any other custom modelfiles

**Location**: Root directory (`/home/dallas/mo11y/`)

## Quick Backup Command

```bash
# Create backup directory with timestamp
BACKUP_DIR="mo11y_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup databases
cp mo11y_companion.db "$BACKUP_DIR/" 2>/dev/null
cp SPOHNZ.db "$BACKUP_DIR/" 2>/dev/null

# Backup life journal
cp life-journal.json "$BACKUP_DIR/" 2>/dev/null

# Backup config (contains API keys - be careful!)
cp config.json "$BACKUP_DIR/" 2>/dev/null

# Backup OAuth token (if exists)
cp token.json "$BACKUP_DIR/" 2>/dev/null || true

# Backup sonas directory
cp -r sonas "$BACKUP_DIR/"

# Backup RAGs directory
cp -r RAGs "$BACKUP_DIR/"

# Backup conversation logs
cp -r conversation_logs "$BACKUP_DIR/" 2>/dev/null || true

# Backup media directory (if exists and has content)
if [ -d media ] && [ "$(ls -A media)" ]; then
    cp -r media "$BACKUP_DIR/"
fi

# Backup custom modelfiles
cp Modelfile.* "$BACKUP_DIR/" 2>/dev/null || true

echo "✅ Backup created in: $BACKUP_DIR"
echo "📦 Compressing backup..."
tar -czf "${BACKUP_DIR}.tar.gz" "$BACKUP_DIR"
echo "✅ Compressed backup: ${BACKUP_DIR}.tar.gz"
```

## What NOT to Back Up

These are code/config files that can be regenerated:

- `*.py` files - Source code (in git)
- `requirements.txt` - Dependencies list
- `*.md` files - Documentation (in git)
- `*.sh` files - Setup scripts (in git)
- `test_*.db` - Test databases
- `.git/` - Git repository (already version controlled)

## Backup Frequency Recommendations

- **Daily**: Databases, life-journal.json (if actively using)
- **Weekly**: SONA files, RAG files, conversation logs
- **Monthly**: Full backup of everything
- **Before major changes**: Always backup before updating personas or RAG files

## Restore Process

To restore from backup:

```bash
# Extract backup
tar -xzf mo11y_backup_YYYYMMDD_HHMMSS.tar.gz

# Restore files
cd mo11y_backup_YYYYMMDD_HHMMSS

# Restore databases
cp mo11y_companion.db /home/dallas/mo11y/
cp SPOHNZ.db /home/dallas/mo11y/

# Restore life journal
cp life-journal.json /home/dallas/mo11y/

# Restore config (be careful with API keys)
cp config.json /home/dallas/mo11y/

# Restore sonas
cp -r sonas/* /home/dallas/mo11y/sonas/

# Restore RAGs
cp -r RAGs/* /home/dallas/mo11y/RAGs/

# Restore conversation logs (optional)
cp -r conversation_logs/* /home/dallas/mo11y/conversation_logs/ 2>/dev/null || true

# Restore media (optional)
cp -r media/* /home/dallas/mo11y/media/ 2>/dev/null || true
```

## Automated Backup Script

Create `backup_mo11y.sh`:

```bash
#!/bin/bash
# Mo11y Personal Data Backup Script

BACKUP_ROOT="${BACKUP_ROOT:-$HOME/mo11y_backups}"
MO11Y_DIR="/home/dallas/mo11y"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/mo11y_backup_$TIMESTAMP"

mkdir -p "$BACKUP_DIR"

echo "📦 Backing up Mo11y personal data..."

# Databases
echo "  📊 Backing up databases..."
cp "$MO11Y_DIR/mo11y_companion.db" "$BACKUP_DIR/" 2>/dev/null
cp "$MO11Y_DIR/SPOHNZ.db" "$BACKUP_DIR/" 2>/dev/null

# Life journal
echo "  📝 Backing up life journal..."
cp "$MO11Y_DIR/life-journal.json" "$BACKUP_DIR/" 2>/dev/null

# Config
echo "  ⚙️  Backing up config..."
cp "$MO11Y_DIR/config.json" "$BACKUP_DIR/" 2>/dev/null

# OAuth token
if [ -f "$MO11Y_DIR/token.json" ]; then
    echo "  🔐 Backing up OAuth token..."
    cp "$MO11Y_DIR/token.json" "$BACKUP_DIR/"
fi

# SONAs
echo "  🎭 Backing up personas..."
cp -r "$MO11Y_DIR/sonas" "$BACKUP_DIR/"

# RAGs
echo "  📚 Backing up RAG files..."
cp -r "$MO11Y_DIR/RAGs" "$BACKUP_DIR/"

# Conversation logs
if [ -d "$MO11Y_DIR/conversation_logs" ]; then
    echo "  💬 Backing up conversation logs..."
    cp -r "$MO11Y_DIR/conversation_logs" "$BACKUP_DIR/"
fi

# Media
if [ -d "$MO11Y_DIR/media" ] && [ "$(ls -A $MO11Y_DIR/media)" ]; then
    echo "  🖼️  Backing up media files..."
    cp -r "$MO11Y_DIR/media" "$BACKUP_DIR/"
fi

# Custom modelfiles
echo "  🤖 Backing up custom modelfiles..."
cp "$MO11Y_DIR"/Modelfile.* "$BACKUP_DIR/" 2>/dev/null || true

# Compress
echo "  📦 Compressing backup..."
cd "$BACKUP_ROOT"
tar -czf "mo11y_backup_$TIMESTAMP.tar.gz" "mo11y_backup_$TIMESTAMP"
rm -rf "mo11y_backup_$TIMESTAMP"

echo "✅ Backup complete: mo11y_backup_$TIMESTAMP.tar.gz"
echo "📁 Location: $BACKUP_ROOT/"
```

Make it executable:
```bash
chmod +x backup_mo11y.sh
```

## Summary Checklist

**Essential (Backup Regularly):**
- ✅ `mo11y_companion.db` or `SPOHNZ.db` (check config.json for which is active)
- ✅ `life-journal.json`
- ✅ `sonas/*.json` (all persona files)
- ✅ `RAGs/*.json` (all RAG files)
- ✅ `config.json` (contains API keys - store securely!)
- ✅ `token.json` (if using Google Calendar)

**Recommended:**
- ✅ `conversation_logs/` (conversation history)
- ✅ `media/` (uploaded media files)
- ✅ `Modelfile.*` (custom modelfiles)

**Optional:**
- `test_*.db` (test databases - can skip)
- `sonas/*.backup` (backup copies - already backed up)

---

**Remember**: Your memories, personality evolution, and personal data are in the databases. Back them up frequently!
