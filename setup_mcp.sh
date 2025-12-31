#!/bin/bash
# Setup script for MCP server

echo "🔧 Setting up MCP Server..."

# Find venv
if [ -d "/home/dallas/venv" ]; then
    VENV="/home/dallas/venv"
elif [ -d "/home/dallas/.venv" ]; then
    VENV="/home/dallas/.venv"
elif [ -d "venv" ]; then
    VENV="venv"
else
    echo "❌ Virtual environment not found. Please activate your venv first."
    exit 1
fi

echo "📦 Installing dependencies..."
$VENV/bin/pip install fastapi uvicorn duckduckgo-search --quiet

echo "✅ Dependencies installed!"
echo ""
echo "🚀 To start MCP server:"
echo "   cd /home/dallas/mo11y"
echo "   source $VENV/bin/activate"
echo "   python local_mcp_server.py"
echo ""
echo "📡 Server will run on: http://localhost:8443"
echo "   (Check config.json - mcp_server_url should match)"
