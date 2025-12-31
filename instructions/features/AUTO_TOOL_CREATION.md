# Automatic Tool Creation

## How It Works

When you chat with **Tool Builder** persona and ask for a tool, Tool Builder will automatically create the files for you!

## Process

1. **You ask**: "Create a tool that searches ../my-life.json for a word"
2. **Tool Builder responds**: Provides code in a specific format
3. **System automatically**:
   - Creates `mcp_tools/your_tool.py`
   - Updates `mcp_tools/__init__.py`
   - Updates `local_mcp_server.py`
4. **You restart**: MCP server to use the new tool

## What Tool Builder Needs to Provide

Tool Builder will automatically format its response with:

1. **File path**: `mcp_tools/tool_name.py`
2. **Python code block**: Complete handler function
3. **Import statement**: For `__init__.py`
4. **Registration code**: For `local_mcp_server.py`

## Example Request

**You**: "Create a tool called life_search that searches ../my-life.json for a word. Put it in mcp_tools/life_search.py"

**Tool Builder will**:
- Generate the code
- System automatically creates the files
- Shows success message
- You restart MCP server

## After Tool Creation

When Tool Builder creates a tool, you'll see:
```
✅ Tool 'life_search' created successfully!

Files created:
- mcp_tools/life_search.py
- Updated mcp_tools/__init__.py
- Updated local_mcp_server.py

🔄 Please restart the MCP server to use the new tool.
```

## Restarting MCP Server

```bash
# Stop current server (Ctrl+C)
python3 local_mcp_server.py
```

## Using the Tool

After restart, you can use the tool via:
- Streamlit UI (Settings → MCP Tools)
- Chat with Alex Mercer (if she uses MCP tools)
- Direct MCP client calls

## Troubleshooting

**Tool not created?**
- Check Tool Builder's response format
- Look for error messages in Streamlit
- Verify code blocks are properly formatted

**Tool created but not working?**
- Check MCP server logs for errors
- Verify tool file syntax is correct
- Make sure MCP server was restarted

**Tool already exists?**
- Delete the old tool file first
- Or ask Tool Builder to modify existing tool

## Benefits

✅ **No manual file creation** - It's automatic!  
✅ **No copy-paste errors** - Code is applied directly  
✅ **Consistent format** - All tools follow same structure  
✅ **Quick testing** - Create and test tools rapidly  
