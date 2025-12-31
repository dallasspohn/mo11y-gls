#!/bin/bash
# Start MCP server and test it

echo "🔧 MCP Server Starter & Tester"
echo "=" | head -c 60; echo ""

# Check if server is already running
if curl -s http://localhost:8443/health > /dev/null 2>&1; then
    echo "✅ Server is already running!"
    python3 check_mcp_server.py
    exit 0
fi

echo "📡 Starting MCP server..."
echo ""
echo "⚠️  IMPORTANT: Keep this terminal open!"
echo "   The server will run in the background"
echo ""

# Start server in background
cd "$(dirname "$0")"
nohup python3 local_mcp_server.py > mcp_server.log 2>&1 &
SERVER_PID=$!

echo "⏳ Waiting for server to start..."
sleep 3

# Check if process is still running
if ! ps -p $SERVER_PID > /dev/null; then
    echo "❌ Server failed to start!"
    echo "   Check mcp_server.log for errors:"
    tail -20 mcp_server.log
    exit 1
fi

# Check if server is responding
if curl -s http://localhost:8443/health > /dev/null 2>&1; then
    echo "✅ Server started successfully!"
    echo ""
    python3 check_mcp_server.py
    echo ""
    echo "💡 Server is running in background (PID: $SERVER_PID)"
    echo "   To stop: kill $SERVER_PID"
    echo "   Or: pkill -f local_mcp_server.py"
else
    echo "❌ Server started but not responding"
    echo "   Check mcp_server.log:"
    tail -20 mcp_server.log
    exit 1
fi
