# Quick Start: Local MCP Server

## 🚀 3-Step Setup

### Step 1: Install Dependencies

```bash
pip install fastapi uvicorn pydantic
```

### Step 2: Start Server

```bash
python3 local_mcp_server.py
```

Server runs on: `http://localhost:8443` (default)

**Note**: Change port with `export MCP_SERVER_PORT=8001` before starting

### Step 3: Update Config

Add to `config.json`:

```json
{
    "mcp_server_url": "http://localhost:8443"
}
```

**Done!** Your existing MCP client code will work automatically.

## ✅ Test It

```bash
python3 test_mcp_connection.py
```

## 🛠️ Add Your First Tool

Edit `local_mcp_server.py`, add this:

```python
def my_first_tool(arguments: Dict) -> Dict:
    """My first custom tool"""
    text = arguments.get("text", "")
    return {
        "content": [{"type": "text", "text": f"You said: {text}"}],
        "isError": False
    }

register_tool(
    name="my_first_tool",
    description="My first custom tool",
    parameters={
        "text": {"type": "string", "description": "Text to process"}
    },
    handler=my_first_tool
)
```

Restart server, and your tool is available!

## 📚 Full Guide

See `LOCAL_MCP_SERVER_SETUP.md` for complete documentation.
