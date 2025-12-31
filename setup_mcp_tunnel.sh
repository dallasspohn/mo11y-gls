#!/bin/bash
# SSH Tunnel Setup for Docker MCP Gateway
# This script sets up an SSH tunnel to access the MCP gateway on the remote server

REMOTE_HOST="192.168.1.224"
REMOTE_PORT="46283"
LOCAL_PORT="46283"

echo "🔗 Setting up SSH tunnel to Docker MCP Gateway"
echo "   Remote: ${REMOTE_HOST}:${REMOTE_PORT}"
echo "   Local:  localhost:${LOCAL_PORT}"
echo ""
echo "Starting SSH tunnel (press Ctrl+C to stop)..."
echo ""

# Check if tunnel is already running
if lsof -Pi :${LOCAL_PORT} -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port ${LOCAL_PORT} is already in use. Killing existing process..."
    lsof -ti:${LOCAL_PORT} | xargs kill -9 2>/dev/null
    sleep 1
fi

# Create SSH tunnel
ssh -N -L ${LOCAL_PORT}:localhost:${REMOTE_PORT} ${REMOTE_HOST} &
TUNNEL_PID=$!

# Wait a moment for tunnel to establish
sleep 2

# Check if tunnel is running
if ps -p $TUNNEL_PID > /dev/null; then
    echo "✅ SSH tunnel established (PID: $TUNNEL_PID)"
    echo "   You can now connect to: http://localhost:${LOCAL_PORT}"
    echo ""
    echo "To stop the tunnel, run: kill $TUNNEL_PID"
    echo "Or press Ctrl+C"
    echo ""
    
    # Save PID to file for easy cleanup
    echo $TUNNEL_PID > /tmp/mcp_tunnel.pid
    echo "PID saved to /tmp/mcp_tunnel.pid"
    
    # Wait for user interrupt
    trap "kill $TUNNEL_PID 2>/dev/null; rm -f /tmp/mcp_tunnel.pid; echo ''; echo 'Tunnel closed.'; exit 0" INT TERM
    wait $TUNNEL_PID
else
    echo "❌ Failed to establish SSH tunnel"
    echo "   Make sure you can SSH to ${REMOTE_HOST}"
    exit 1
fi
