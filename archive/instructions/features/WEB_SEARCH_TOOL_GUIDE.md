# Web Search Tool Guide

## Overview

I've added a **web search tool** to your local MCP server and integrated it into the Streamlit dashboard. You can now search the web directly from the interface!

## Setup

### 1. Install DuckDuckGo Search Library

```bash
pip install duckduckgo-search
```

### 2. Start MCP Server

```bash
python3 local_mcp_server.py
```

The web search tool is automatically registered!

### 3. Update Config (if needed)

Make sure `config.json` has:

```json
{
    "mcp_server_url": "http://localhost:8443"
}
```

**Note**: Default port is 8443. Change with `export MCP_SERVER_PORT=8001` if needed.

## Using Web Search from Dashboard

### Method 1: Quick Search in Sidebar

1. **Open Streamlit dashboard**: `streamlit run app_enhanced.py`
2. **Scroll to sidebar** → Look for "🔧 MCP Tools" section
3. **Find "🔍 Web Search"** section
4. **Enter your query** in the search box
5. **Adjust max results** (slider, 1-10)
6. **Click "🔍 Search"**

Results will appear below with:
- Title
- URL
- Snippet/preview

**Bonus**: Click "💬 Add to Conversation" to add search results to your chat!

### Method 2: Call from Chat

You can also ask the agent to search:

```
"Search the web for latest AI news"
"Look up information about Python async programming"
"Find recent articles about LangGraph"
```

The agent will automatically use the `web_search` tool when it detects you want web information.

## Using Web Search Programmatically

### From Python Code

```python
from mcp_connection import MCPClient

client = MCPClient(mcp_server_url="http://localhost:8443")

# Search the web
result = client.call_tool(
    "web_search",
    {
        "query": "latest AI developments 2025",
        "max_results": 5
    }
)

# Print results
if result and result.get("content"):
    print(result["content"][0]["text"])
```

### From Agent

```python
from mo11y_agent import create_mo11y_agent

agent = create_mo11y_agent(
    model_name="deepseek-r1:latest",
    enable_mcp=True
)

# Agent can use web search automatically
response = agent.chat("What's the latest news about AI?")
```

## Tool Parameters

- **`query`** (required): Your search query string
- **`max_results`** (optional): Number of results to return (default: 5, max: 10)

## Example Searches

Try these in the dashboard:

- "Python async programming best practices"
- "Latest LangGraph updates"
- "Ollama model comparison 2025"
- "FastAPI vs Flask performance"
- "Streamlit tips and tricks"

## How It Works

1. **DuckDuckGo Search**: Uses the `duckduckgo-search` library (no API key needed!)
2. **MCP Protocol**: Implements standard MCP JSON-RPC 2.0
3. **Results Format**: Returns formatted text with titles, URLs, and snippets
4. **Error Handling**: Gracefully handles errors and missing dependencies

## Troubleshooting

### "DuckDuckGo search not available"

Install the library:
```bash
pip install duckduckgo-search
```

### No results returned

- Check your internet connection
- Try a different search query
- Check server logs for errors

### Tool not showing in dashboard

- Make sure MCP server is running
- Verify `mcp_server_url` in config.json
- Check that agent has `enable_mcp=True`

## Adding More Search Tools

Want to add Google Search, Bing, or other search engines? Edit `local_mcp_server.py`:

```python
def google_search_tool(arguments: Dict) -> Dict:
    """Search using Google (requires API key)"""
    # Implementation here
    pass

register_tool(
    name="google_search",
    description="Search using Google",
    parameters={
        "query": {"type": "string", "description": "Search query"},
        "api_key": {"type": "string", "description": "Google API key"}
    },
    handler=google_search_tool
)
```

## Integration with Agent

The agent automatically detects when you need web information and can use the search tool:

```
User: "What's happening with AI today?"
Agent: [Uses web_search tool] "Based on recent web search results..."
```

## Summary

✅ **Web search tool** added to MCP server  
✅ **Dashboard integration** - Search directly from sidebar  
✅ **Chat integration** - Agent can search automatically  
✅ **No API key needed** - Uses DuckDuckGo (free)  
✅ **Easy to extend** - Add more search engines easily  

Just install `duckduckgo-search`, start the server, and start searching! 🔍
