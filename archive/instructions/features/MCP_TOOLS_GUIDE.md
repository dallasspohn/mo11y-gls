# MCP Tools Usage Guide

This guide will help you test and use each MCP tool one at a time.

## Prerequisites

1. **MCP Server Running**: Make sure `local_mcp_server.py` is running:
   ```bash
   python3 local_mcp_server.py
   ```
   You should see: `📡 Server will be available at: http://localhost:8443`

2. **Config Set**: Your `config.json` should have:
   ```json
   {
     "mcp_server_url": "http://localhost:8443"
   }
   ```

## Quick Test Script

Run the test script to test all tools:
```bash
python3 test_mcp_tools.py
```

This will test each tool one at a time with examples.

## Tool-by-Tool Guide

### 1. Echo Tool (Simplest Test)

**Purpose**: Echo back text - simplest way to verify the connection works.

**How to test manually**:
```python
from mcp_connection import MCPClient

client = MCPClient(mcp_server_url="http://localhost:8443")
result = client.call_tool("echo", {"text": "Hello!"})
print(result)
```

**Expected output**: `{"content": [{"type": "text", "text": "Echo: Hello!"}], "isError": False}`

**Use case**: Testing that MCP connection works.

---

### 2. Calculator Tool

**Purpose**: Evaluate mathematical expressions.

**How to test manually**:
```python
from mcp_connection import MCPClient

client = MCPClient(mcp_server_url="http://localhost:8443")
result = client.call_tool("calculator", {"expression": "2 + 2 * 3"})
print(result)
```

**Expected output**: `{"content": [{"type": "text", "text": "Result: 8"}], "isError": False}`

**Use case**: Math calculations in conversations.

**Example expressions**:
- `"2 + 2"`
- `"10 * 5 - 3"`
- `"(100 + 50) / 2"`

---

### 3. Web Search Tool

**Purpose**: Search the web using DuckDuckGo (no API key needed!).

**Requirements**: 
- `duckduckgo-search` library installed: `pip install duckduckgo-search`

**How to test manually**:
```python
from mcp_connection import MCPClient

client = MCPClient(mcp_server_url="http://localhost:8443")
result = client.call_tool("web_search", {
    "query": "Python programming",
    "max_results": 3
})
print(result)
```

**Expected output**: Search results with titles, URLs, and snippets.

**Use case**: Getting current information, news, facts.

**Parameters**:
- `query` (required): Search query string
- `max_results` (optional): Number of results (default: 5)

**Example queries**:
- `"latest Python news"`
- `"weather in Dallas TX"`
- `"spohnz.com"`

---

### 4. Ollama Chat Tool

**Purpose**: Chat with an Ollama model directly.

**Requirements**:
- Ollama running: `ollama serve`
- Model pulled: `ollama pull llama3.2:3b` (or your preferred model)

**How to test manually**:
```python
from mcp_connection import MCPClient

client = MCPClient(mcp_server_url="http://localhost:8443")
result = client.call_tool("ollama_chat", {
    "model": "llama3.2:3b",
    "message": "Say hello in one sentence"
})
print(result)
```

**Expected output**: Model's response text.

**Use case**: Direct model interaction, testing models.

**Parameters**:
- `model` (required): Ollama model name (e.g., "llama3.2:3b", "deepseek-r1:latest")
- `message` (required): Message to send to the model

---

## Using Tools in the Agent

The agent automatically uses tools when appropriate:

1. **Web Search**: Automatically triggered when you ask about:
   - Current information ("latest", "recent", "now", "today")
   - Websites (".com", ".org", etc.)
   - Questions like "tell me about X"

2. **Calculator**: Can be called manually via the Settings page → MCP Tools

3. **Echo**: Mainly for testing

4. **Ollama Chat**: Can be called manually via the Settings page → MCP Tools

## Troubleshooting

### Tool not working?

1. **Check server is running**:
   ```bash
   curl http://localhost:8443/
   ```
   Should return JSON-RPC response or error (not connection refused)

2. **Check config.json**:
   ```json
   {
     "mcp_server_url": "http://localhost:8443"
   }
   ```

3. **Test connection**:
   ```bash
   python3 test_mcp_connection.py
   ```

4. **Check tool availability**:
   ```python
   from mcp_connection import MCPClient
   client = MCPClient(mcp_server_url="http://localhost:8443")
   tools = client.list_tools()
   print([t['name'] for t in tools])
   ```

### Web Search not working?

- Install: `pip install duckduckgo-search`
- Check server output shows: `DuckDuckGo search available: True`

### Ollama Chat not working?

- Start Ollama: `ollama serve`
- Pull a model: `ollama pull llama3.2:3b`
- Check server output shows: `Ollama available: True`

## Next Steps

Once tools are working:

1. **In Chat**: Ask questions that trigger web search automatically
2. **In Settings**: Use the MCP Tools section to call tools manually
3. **Custom Tools**: Add your own tools to `local_mcp_server.py`

## Example: Testing Web Search

```python
# Quick test script
from mcp_connection import MCPClient

client = MCPClient(mcp_server_url="http://localhost:8443")

# Test web search
result = client.call_tool("web_search", {
    "query": "Python 3.12 features",
    "max_results": 3
})

if result and result.get("content"):
    print(result["content"][0]["text"])
else:
    print("Error:", result)
```

This should return search results about Python 3.12 features!
