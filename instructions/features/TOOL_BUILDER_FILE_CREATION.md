# Tool Builder File Creation

## Important Note

**Tool Builder provides the CODE, but YOU need to CREATE THE FILES.**

Tool Builder is an AI assistant that generates code - it cannot directly create files on your system. You need to:

1. Copy the code Tool Builder provides
2. Create the files manually
3. Paste the code into those files

## Workflow

### Step 1: Tool Builder Provides Code

Tool Builder will show you:
- Complete Python code for the tool file
- Import line for `__init__.py`
- Registration code for `local_mcp_server.py`

### Step 2: You Create the Files

**Create**: `mcp_tools/your_tool.py`
- Copy the handler function code
- Paste into new file
- Save

**Update**: `mcp_tools/__init__.py`
- Add the import line Tool Builder shows
- Add to `__all__` list

**Update**: `local_mcp_server.py`
- Add the registration code Tool Builder shows
- Place it in the "Load custom tools" section

### Step 3: Restart MCP Server

```bash
# Stop current server (Ctrl+C)
# Restart
python3 local_mcp_server.py
```

### Step 4: Test

Use the tool via Streamlit UI or MCP client.

## Example: Text Case Tool

Tool Builder provided code for `textcase.py` - I've created it for you as an example. You can see:
- `mcp_tools/textcase.py` - The tool handler
- `mcp_tools/__init__.py` - Updated with import
- `local_mcp_server.py` - Updated with registration

## Future Automation

A helper script (`create_mcp_tool.py`) exists but needs enhancement to fully automate this. For now, manual file creation is required.

## Quick Copy-Paste Workflow

1. Tool Builder shows code → Copy it
2. Create file → Paste code → Save
3. Update `__init__.py` → Add import
4. Update `local_mcp_server.py` → Add registration
5. Restart server → Test tool

This is a one-time setup per tool - once created, the tool is available permanently!
