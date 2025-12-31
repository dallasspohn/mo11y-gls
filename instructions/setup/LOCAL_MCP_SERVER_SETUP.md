# Local MCP Server Setup Guide

## Overview

This guide shows you how to build and run a **local MCP server** using Python, FastAPI, LangGraph, and Ollama. This replaces the Docker Desktop MCP server and runs entirely on your machine.

## ✅ Compatibility

**Yes, your existing API instructions will work the same!** The server implements the standard MCP JSON-RPC 2.0 protocol, so your existing `MCPClient` code will work without any changes.

## Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn pydantic
pip install ollama  # Optional, for Ollama integration
pip install langgraph  # Optional, for LangGraph integration
```

### 2. Start the Server

```bash
python3 local_mcp_server.py
```

The server will start on `http://localhost:8443` (default)

**Note**: You can change the port by setting `MCP_SERVER_PORT` environment variable:
```bash
export MCP_SERVER_PORT=8001  # Use a different port
python3 local_mcp_server.py
```

### 3. Update Your Config

Add to `config.json`:

```json
{
    "mcp_server_url": "http://localhost:8443"
}
```

Or set environment variable:

```bash
export MCP_SERVER_URL="http://localhost:8443"
```

### 4. Test It

```bash
python3 test_mcp_connection.py
```

## Server Features

### Built-in Tools

1. **echo** - Echo back text
2. **calculator** - Evaluate mathematical expressions
3. **ollama_chat** - Chat with Ollama models (if Ollama installed)

### Built-in Resources

1. **local://server-info** - Server information
2. **local://tools-list** - List of available tools

### Built-in Prompts

1. **greeting** - Generate a greeting message

## Creating Your Own Tools

### Simple Tool Example

Add this to `local_mcp_server.py`:

```python
def my_custom_tool(arguments: Dict) -> Dict:
    """Your tool description"""
    # Get arguments
    param1 = arguments.get("param1", "")
    
    # Do your work here
    result = f"Processed: {param1}"
    
    # Return result
    return {
        "content": [
            {
                "type": "text",
                "text": result
            }
        ],
        "isError": False
    }

# Register it
register_tool(
    name="my_tool",
    description="What your tool does",
    parameters={
        "param1": {
            "type": "string",
            "description": "Parameter description"
        }
    },
    handler=my_custom_tool
)
```

### LangGraph Tool Example

```python
from langgraph.graph import StateGraph, END

def langgraph_tool(arguments: Dict) -> Dict:
    """Tool using LangGraph"""
    if not LANGGRAPH_AVAILABLE:
        return {
            "content": [{"type": "text", "text": "LangGraph not available"}],
            "isError": True
        }
    
    # Create a simple graph
    workflow = StateGraph(dict)
    workflow.add_node("process", lambda x: {"result": f"Processed: {x.get('input', '')}"})
    workflow.set_entry_point("process")
    workflow.add_edge("process", END)
    
    app = workflow.compile()
    result = app.invoke({"input": arguments.get("input", "")})
    
    return {
        "content": [{"type": "text", "text": str(result)}],
        "isError": False
    }

register_tool(
    name="langgraph_process",
    description="Process input using LangGraph",
    parameters={
        "input": {
            "type": "string",
            "description": "Input to process"
        }
    },
    handler=langgraph_tool
)
```

### Ollama Tool Example

```python
def ollama_tool(arguments: Dict) -> Dict:
    """Tool using Ollama"""
    if not OLLAMA_AVAILABLE:
        return {
            "content": [{"type": "text", "text": "Ollama not available"}],
            "isError": True
        }
    
    model = arguments.get("model", "deepseek-r1:latest")
    prompt = arguments.get("prompt", "")
    
    response = chat(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return {
        "content": [
            {
                "type": "text",
                "text": response.get("message", {}).get("content", "")
            }
        ],
        "isError": False
    }

register_tool(
    name="my_ollama_tool",
    description="Use Ollama for something",
    parameters={
        "model": {
            "type": "string",
            "description": "Ollama model name"
        },
        "prompt": {
            "type": "string",
            "description": "Prompt to send"
        }
    },
    handler=ollama_tool
)
```

## Creating Resources

```python
def read_my_resource(uri: str) -> Dict:
    """Read a custom resource"""
    # Load from file, database, etc.
    content = "Your resource content here"
    
    return {
        "contents": [
            {
                "uri": uri,
                "mimeType": "text/plain",
                "text": content
            }
        ]
    }

# Register resource
register_resource(
    uri="local://my-resource",
    name="My Resource",
    description="Description of your resource",
    mime_type="text/plain"
)
```

## Creating Prompts

```python
register_prompt(
    name="my_prompt",
    description="Generate a custom prompt",
    arguments=["name", "topic"],
    template="Hello {name}, let's talk about {topic}."
)
```

## Running as a Service

### Using systemd (Linux)

Create `/etc/systemd/user/local-mcp-server.service`:

```ini
[Unit]
Description=Local MCP Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/dallas/dev/mo11y
ExecStart=/usr/bin/python3 /home/dallas/dev/mo11y/local_mcp_server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Then:

```bash
systemctl --user enable local-mcp-server.service
systemctl --user start local-mcp-server.service
```

### Using screen/tmux

```bash
# Start in screen
screen -S mcp-server
python3 local_mcp_server.py

# Detach: Ctrl+A, then D
# Reattach: screen -r mcp-server
```

### Using nohup

```bash
nohup python3 local_mcp_server.py > mcp-server.log 2>&1 &
```

## Testing Your Tools

### Using Python

```python
from mcp_connection import MCPClient

client = MCPClient(mcp_server_url="http://localhost:8443")

# List tools
tools = client.list_tools()
print(f"Available tools: {[t['name'] for t in tools]}")

# Call a tool
result = client.call_tool("echo", {"text": "Hello!"})
print(result)
```

### Using curl

```bash
# List tools
curl -X POST http://localhost:8443 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'

# Call a tool
curl -X POST http://localhost:8443 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "echo",
      "arguments": {"text": "Hello World"}
    }
  }'
```

## Integration with Mo11y Agent

Your existing agent code will work automatically:

```python
from mo11y_agent import create_mo11y_agent

agent = create_mo11y_agent(
    model_name="deepseek-r1:latest",
    enable_mcp=True  # Will connect to http://localhost:8443
)

# Agent can now use your tools!
result = agent.chat("Use the echo tool to say hello")
```

## Advanced: Using LangGraph for Tool Orchestration

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class ToolState(TypedDict):
    input: str
    result: str
    tools_used: List[str]

def orchestrate_tools(state: ToolState) -> ToolState:
    """Orchestrate multiple tools"""
    # Use LangGraph to chain tools together
    # Example: tool1 -> tool2 -> tool3
    pass

# Create graph
workflow = StateGraph(ToolState)
workflow.add_node("process", orchestrate_tools)
workflow.set_entry_point("process")
workflow.add_edge("process", END)

app = workflow.compile()
```

## Troubleshooting

### Server won't start

- Check if port 8443 is available: `lsof -i :8443`
- Change port by setting `MCP_SERVER_PORT` environment variable:
  ```bash
  export MCP_SERVER_PORT=8001
  python3 local_mcp_server.py
  ```

### Tools not showing

- Check server logs for errors
- Verify tool registration code runs
- Test with `curl` or `test_mcp_connection.py`

### Connection refused

- Make sure server is running: `curl http://localhost:8443/health`
- Check firewall settings
- Verify `MCP_SERVER_URL` is correct

## Next Steps

1. **Start the server**: `python3 local_mcp_server.py`
2. **Add your tools**: Edit `local_mcp_server.py` and add `register_tool()` calls
3. **Test**: Use `test_mcp_connection.py` or curl
4. **Integrate**: Your Mo11y agent will automatically use the tools

## Example: Complete Tool with LangGraph + Ollama

```python
def smart_processor_tool(arguments: Dict) -> Dict:
    """Process input with LangGraph, then use Ollama"""
    if not LANGGRAPH_AVAILABLE or not OLLAMA_AVAILABLE:
        return {"content": [{"type": "text", "text": "Dependencies not available"}], "isError": True}
    
    input_text = arguments.get("input", "")
    
    # Step 1: Process with LangGraph
    workflow = StateGraph(dict)
    workflow.add_node("preprocess", lambda x: {"processed": f"Preprocessed: {x.get('input', '')}"})
    workflow.set_entry_point("preprocess")
    workflow.add_edge("preprocess", END)
    
    app = workflow.compile()
    graph_result = app.invoke({"input": input_text})
    
    # Step 2: Use Ollama
    ollama_result = chat(
        model="deepseek-r1:latest",
        messages=[{"role": "user", "content": graph_result.get("processed", "")}]
    )
    
    return {
        "content": [
            {
                "type": "text",
                "text": ollama_result.get("message", {}).get("content", "")
            }
        ],
        "isError": False
    }

register_tool(
    name="smart_processor",
    description="Process input with LangGraph then Ollama",
    parameters={
        "input": {
            "type": "string",
            "description": "Input text to process"
        }
    },
    handler=smart_processor_tool
)
```

## Summary

✅ **Simple setup** - Just `pip install` and run  
✅ **Compatible** - Works with existing MCP client code  
✅ **Extensible** - Easy to add new tools  
✅ **Local** - No Docker, no remote server  
✅ **LangGraph ready** - Can use LangGraph for orchestration  
✅ **Ollama ready** - Can use Ollama for LLM capabilities  

Your existing API instructions work exactly the same - just point `MCP_SERVER_URL` to `http://localhost:8443`!
