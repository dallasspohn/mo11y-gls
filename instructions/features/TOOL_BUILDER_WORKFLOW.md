# Tool Builder Workflow

## How Tool Builder Creates Tools

Tool Builder now creates tools as **separate files** in the `mcp_tools/` directory, not directly in `local_mcp_server.py`.

## Workflow

### 1. User Requests Tool
**You**: "Create a tool that reads a text file and returns its contents"

### 2. Tool Builder Generates Three Things

#### A. Tool File: `mcp_tools/file_reader.py`
Complete Python file with the tool handler function.

#### B. Update: `mcp_tools/__init__.py`
Add import line to export the tool.

#### C. Update: `local_mcp_server.py`
Add registration code to register the tool.

### 3. You Apply the Changes

1. Create the tool file in `mcp_tools/`
2. Update `mcp_tools/__init__.py`
3. Update `local_mcp_server.py`
4. Restart MCP server

### 4. Test the Tool

Use via MCP client or Streamlit UI.

## Example: File Reader Tool

Tool Builder will provide:

**File 1**: `mcp_tools/file_reader.py`
```python
from typing import Dict

def file_reader_tool(arguments: Dict) -> Dict:
    # ... tool code ...
```

**File 2**: Update `mcp_tools/__init__.py`
```python
from .file_reader import file_reader_tool
```

**File 3**: Update `local_mcp_server.py`
```python
from mcp_tools import file_reader_tool

register_tool(
    name="file_reader",
    description="Reads a text file...",
    parameters={...},
    handler=file_reader_tool
)
```

## Benefits

✅ **Better Organization**: Each tool in its own file  
✅ **Easier Maintenance**: Find and edit tools easily  
✅ **No Conflicts**: Don't edit main server file  
✅ **Reusable**: Tools can be imported elsewhere  
✅ **Cleaner**: Server file stays focused  

## Simple Test Tasks

Start with these simple tools:

1. **File Reader** - Reads text files
2. **Text Case Converter** - Uppercase/lowercase
3. **Current Date/Time** - Returns current time
4. **Directory Lister** - Lists files in directory
5. **Word Counter** - Counts words in text

Avoid complex tools like network scanners initially - they can cause high CPU usage.
