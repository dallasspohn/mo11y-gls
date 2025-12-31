# MCP Tools Directory

This directory contains custom MCP tools as separate Python files. Each tool is in its own file for better organization and maintainability.

## Structure

```
mcp_tools/
├── __init__.py          # Exports all tools
├── file_reader.py      # Example: File reader tool
└── README.md           # This file
```

## Adding a New Tool

### Step 1: Create Tool File

Create a new file: `mcp_tools/your_tool_name.py`

```python
"""
Your Tool Description
"""

from typing import Dict


def your_tool_handler(arguments: Dict) -> Dict:
    """
    Tool description
    
    Args:
        arguments: Dictionary containing tool parameters
    
    Returns:
        Dictionary with "content" array and "isError" flag
    """
    try:
        # Extract parameters
        param = arguments.get("param")
        
        # Validate
        if not param:
            return {
                "content": [{"type": "text", "text": "Error: param is required"}],
                "isError": True
            }
        
        # Do the work
        result = do_something(param)
        
        # Return JSON-RPC format
        return {
            "content": [{"type": "text", "text": str(result)}],
            "isError": False
        }
    
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }
```

### Step 2: Update __init__.py

Add import to `mcp_tools/__init__.py`:

```python
from .your_tool_name import your_tool_handler

__all__ = [..., 'your_tool_handler']
```

### Step 3: Register in Server

Add registration to `local_mcp_server.py` (after existing tool registrations):

```python
from mcp_tools import your_tool_handler

register_tool(
    name="your_tool",
    description="What the tool does",
    parameters={
        "param": {
            "type": "string",
            "description": "Parameter description"
        }
    },
    handler=your_tool_handler
)
```

## Example Tools

- **file_reader.py** - Reads text files and returns contents

## Testing

After adding a tool:

1. Restart MCP server: `python3 local_mcp_server.py`
2. Test via MCP client or Streamlit UI
3. Check server logs for any errors

## Best Practices

- ✅ One tool per file
- ✅ Descriptive file names
- ✅ Proper error handling
- ✅ Input validation
- ✅ Clear docstrings
- ✅ Follow JSON-RPC format
