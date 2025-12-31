#!/bin/bash
# Mo11y Personal Data Backup Script

BACKUP_ROOT="${BACKUP_ROOT:-$HOME/mo11y_backups}"
MO11Y_DIR="/home/dallas/mo11y"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/mo11y_backup_$TIMESTAMP"

mkdir -p "$BACKUP_DIR"

echo "📦 Backing up Mo11y personal data..."
echo ""

# Databases
echo "  📊 Backing up databases..."
cp "$MO11Y_DIR/mo11y_companion.db" "$BACKUP_DIR/" 2>/dev/null && echo "    ✅ mo11y_companion.db" || echo "    ⚠️  mo11y_companion.db not found"
cp "$MO11Y_DIR/SPOHNZ.db" "$BACKUP_DIR/" 2>/dev/null && echo "    ✅ SPOHNZ.db" || echo "    ⚠️  SPOHNZ.db not found"

# Life journal
echo "  📝 Backing up life journal..."
cp "$MO11Y_DIR/life-journal.json" "$BACKUP_DIR/" 2>/dev/null && echo "    ✅ life-journal.json" || echo "    ⚠️  life-journal.json not found"

# Config
echo "  ⚙️  Backing up config..."
cp "$MO11Y_DIR/config.json" "$BACKUP_DIR/" 2>/dev/null && echo "    ✅ config.json" || echo "    ⚠️  config.json not found"

# OAuth token
if [ -f "$MO11Y_DIR/token.json" ]; then
    echo "  🔐 Backing up OAuth token..."
    cp "$MO11Y_DIR/token.json" "$BACKUP_DIR/" && echo "    ✅ token.json"
fi

# SONAs
echo "  🎭 Backing up personas..."
if [ -d "$MO11Y_DIR/sonas" ]; then
    cp -r "$MO11Y_DIR/sonas" "$BACKUP_DIR/" && echo "    ✅ sonas/ directory"
else
    echo "    ⚠️  sonas/ directory not found"
fi

# RAGs
echo "  📚 Backing up RAG files..."
if [ -d "$MO11Y_DIR/RAGs" ]; then
    cp -r "$MO11Y_DIR/RAGs" "$BACKUP_DIR/" && echo "    ✅ RAGs/ directory"
else
    echo "    ⚠️  RAGs/ directory not found"
fi

# Conversation logs
if [ -d "$MO11Y_DIR/conversation_logs" ]; then
    echo "  💬 Backing up conversation logs..."
    cp -r "$MO11Y_DIR/conversation_logs" "$BACKUP_DIR/" && echo "    ✅ conversation_logs/ directory"
fi

# Media
if [ -d "$MO11Y_DIR/media" ] && [ "$(ls -A $MO11Y_DIR/media 2>/dev/null)" ]; then
    echo "  🖼️  Backing up media files..."
    cp -r "$MO11Y_DIR/media" "$BACKUP_DIR/" && echo "    ✅ media/ directory"
fi

# Custom modelfiles
echo "  🤖 Backing up custom modelfiles..."
MODELFILES=$(find "$MO11Y_DIR" -maxdepth 1 -name "Modelfile.*" 2>/dev/null)
if [ -n "$MODELFILES" ]; then
    cp "$MO11Y_DIR"/Modelfile.* "$BACKUP_DIR/" 2>/dev/null && echo "    ✅ Modelfile.*"
else
    echo "    ℹ️  No custom modelfiles found"
fi

# Compress
echo ""
echo "  📦 Compressing backup..."
cd "$BACKUP_ROOT"
tar -czf "mo11y_backup_$TIMESTAMP.tar.gz" "mo11y_backup_$TIMESTAMP" 2>/dev/null
if [ $? -eq 0 ]; then
    rm -rf "mo11y_backup_$TIMESTAMP"
    BACKUP_SIZE=$(du -h "mo11y_backup_$TIMESTAMP.tar.gz" | cut -f1)
    echo "    ✅ Compressed successfully"
    echo ""
    echo "✅ Backup complete!"
    echo "📁 File: mo11y_backup_$TIMESTAMP.tar.gz"
    echo "📊 Size: $BACKUP_SIZE"
    echo "📍 Location: $BACKUP_ROOT/"
else
    echo "    ⚠️  Compression failed, keeping uncompressed backup"
    echo ""
    echo "✅ Backup complete (uncompressed)"
    echo "📁 Directory: $BACKUP_DIR"
fi
