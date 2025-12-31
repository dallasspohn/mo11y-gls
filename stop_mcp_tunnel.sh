#!/bin/bash
# Stop the SSH tunnel for Docker MCP Gateway

if [ -f /tmp/mcp_tunnel.pid ]; then
    TUNNEL_PID=$(cat /tmp/mcp_tunnel.pid)
    if ps -p $TUNNEL_PID > /dev/null; then
        echo "🛑 Stopping SSH tunnel (PID: $TUNNEL_PID)..."
        kill $TUNNEL_PID
        rm -f /tmp/mcp_tunnel.pid
        echo "✅ Tunnel stopped"
    else
        echo "⚠️  Tunnel PID not found (may have already stopped)"
        rm -f /tmp/mcp_tunnel.pid
    fi
else
    echo "⚠️  No tunnel PID file found"
    echo "   Trying to find and kill any tunnel on port 46283..."
    lsof -ti:46283 | xargs kill -9 2>/dev/null && echo "✅ Killed processes on port 46283" || echo "   No processes found on port 46283"
fi
