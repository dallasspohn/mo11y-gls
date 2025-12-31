#!/bin/bash
# Start MCP Server Script

echo "🚀 Starting Local MCP Server..."
echo ""

# Check if port 8443 is in use
if lsof -Pi :8443 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8443 is already in use!"
    echo "   Either stop the existing service or set MCP_SERVER_PORT to a different port"
    echo ""
    echo "   To use a different port:"
    echo "   export MCP_SERVER_PORT=8001"
    echo "   python3 local_mcp_server.py"
    exit 1
fi

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Not in a virtual environment. Activating venv..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "❌ No venv directory found. Please activate your virtual environment first."
        exit 1
    fi
fi

# Check if required packages are installed
python3 -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Required packages not installed. Installing..."
    pip install fastapi uvicorn pydantic duckduckgo-search
fi

echo "📡 Starting server on port 8443..."
echo "   Access at: http://localhost:8443"
echo "   Health check: http://localhost:8443/health"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""

python3 local_mcp_server.py
