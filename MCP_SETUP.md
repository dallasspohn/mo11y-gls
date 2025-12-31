# MCP Tooling Setup Guide

## Current Status

✅ **Code is ready** - MCP server and client code exists
❌ **Dependencies missing** - FastAPI and uvicorn not installed
❌ **Server not running** - MCP server needs to be started

## Quick Setup

### 1. Install Dependencies

```bash
cd /home/dallas/mo11y
source /home/dallas/venv/bin/activate
pip install fastapi uvicorn duckduckgo-search
```

### 2. Test MCP Server

```bash
cd /home/dallas/mo11y
source /home/dallas/venv/bin/activate
python local_mcp_server.py
```

You should see:
```
🚀 Starting Local MCP Server...
📡 Server will be available at: http://localhost:8443
🔍 Available tools:
   - echo
   - calculator
   - web_search
   - generate_image
   ...
```

### 3. Configure Agent to Use MCP

Check `config.json` for MCP settings:
```json
{
  "mcp_server_url": "http://localhost:8443",
  "enable_mcp": true
}
```

### 4. Run as Service (Optional)

Install the systemd service:
```bash
sudo cp mo11y-mcp-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mo11y-mcp-server.service
sudo systemctl start mo11y-mcp-server.service
```

## Available Tools

- **web_search** - Search the web using DuckDuckGo
- **generate_image** - Generate images using Stable Diffusion
- **file_reader** - Read text files
- **textcase** - Convert text case
- **calculator** - Evaluate math expressions
- **echo** - Echo back text (testing)

## Testing

1. Start MCP server: `python local_mcp_server.py`
2. In another terminal, test health:
   ```bash
   curl http://localhost:8443/health
   ```
3. Start Streamlit and ask Alex to use a tool

## Troubleshooting

- **Port conflicts**: Change port with `export MCP_SERVER_PORT=8000`
- **Import errors**: Install missing packages with pip
- **Connection errors**: Check firewall and that server is running
