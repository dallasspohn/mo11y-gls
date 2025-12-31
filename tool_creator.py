"""
Tool Creator - Automatically creates MCP tools from Tool Builder's code
Parses Tool Builder responses and creates tool files automatically
"""

import re
import os
import json
from pathlib import Path
from typing import Dict, Optional, Tuple


def extract_tool_code_from_response(response: str) -> Optional[Dict]:
    """
    Extract tool creation information from Tool Builder's response
    
    Returns:
        Dict with:
            - tool_name: name of the tool
            - handler_function_name: name of the handler function
            - tool_file_code: complete Python code for the tool file
            - init_import_line: import line for __init__.py
            - registration_code: registration code for local_mcp_server.py
            - parameters: tool parameters dict
            - description: tool description
    """
    result = {
        "tool_name": None,
        "handler_function_name": None,
        "tool_file_code": None,
        "init_import_line": None,
        "registration_code": None,
        "parameters": {},
        "description": ""
    }
    
    # Try to find tool file name (e.g., "mcp_tools/life_search.py" or "life_search.py")
    # Multiple patterns to catch different formats
    file_patterns = [
        r'mcp_tools[/\\]([\w_]+)\.py',
        r'File to Create.*?mcp_tools[/\\]([\w_]+)\.py',
        r'Create.*?([\w_]+)\.py',
        r'(\w+)_handler|(\w+)_tool',
        r'def\s+(\w+)\s*\(.*?arguments.*?Dict.*?\)'
    ]
    
    for pattern in file_patterns:
        file_match = re.search(pattern, response, re.IGNORECASE)
        if file_match:
            result["tool_name"] = file_match.group(1) or file_match.group(2) or file_match.group(3)
            if result["tool_name"]:
                break
    
    # Try to find Python code block (multiple formats)
    code_block_patterns = [
        r'```python\s*(.*?)```',  # Standard markdown
        r'```\s*(.*?)```',  # Code block without language
        r'File to Create.*?```python\s*(.*?)```',  # Code after "File to Create"
    ]
    
    tool_code = None
    for pattern in code_block_patterns:
        code_blocks = re.findall(pattern, response, re.DOTALL)
        if code_blocks:
            # First code block is usually the tool handler
            tool_code = code_blocks[0].strip()
            if tool_code and ('def ' in tool_code or 'import ' in tool_code):
                result["tool_file_code"] = tool_code
                break
    
    if tool_code:
        # Extract handler function name
        handler_match = re.search(r'def\s+([\w_]+)\s*\(.*?arguments.*?Dict', tool_code, re.IGNORECASE | re.DOTALL)
        if not handler_match:
            handler_match = re.search(r'def\s+([\w_]+)\s*\(', tool_code)
        if handler_match:
            result["handler_function_name"] = handler_match.group(1)
    
    # Try to find __init__.py update (multiple formats)
    init_patterns = [
        r'from\s+\.([\w_]+)\s+import\s+([\w_]+)',
        r'Update.*?__init__.*?from\s+\.([\w_]+)\s+import\s+([\w_]+)',
        r'mcp_tools/__init__\.py.*?from\s+\.([\w_]+)\s+import\s+([\w_]+)',
    ]
    
    for pattern in init_patterns:
        init_match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
        if init_match:
            result["init_import_line"] = f"from .{init_match.group(1)} import {init_match.group(2)}"
            if not result["handler_function_name"]:
                result["handler_function_name"] = init_match.group(2)
            if not result["tool_name"]:
                result["tool_name"] = init_match.group(1)
            break
    
    # Try to find registration code
    register_pattern = r'register_tool\s*\((.*?)\)'
    register_match = re.search(register_pattern, response, re.DOTALL)
    if register_match:
        registration_text = register_match.group(1)
        result["registration_code"] = f"register_tool({registration_text})"
        
        # Extract tool name from registration
        name_match = re.search(r'name\s*=\s*["\']([\w_]+)["\']', registration_text)
        if name_match and not result["tool_name"]:
            result["tool_name"] = name_match.group(1)
        
        # Extract description
        desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', registration_text)
        if desc_match:
            result["description"] = desc_match.group(1)
        
        # Extract parameters
        params_match = re.search(r'parameters\s*=\s*(\{.*?\})', registration_text, re.DOTALL)
        if params_match:
            try:
                # Try to parse as JSON-like dict
                params_str = params_match.group(1)
                # Clean up the string to make it valid Python dict
                params_str = params_str.replace("'", '"')  # Simple quote conversion
                result["parameters"] = json.loads(params_str)
            except:
                # If parsing fails, store as string for manual review
                result["parameters"] = params_str
    
    # If we have tool code but missing tool_name, try to infer from handler function name
    if result["tool_file_code"] and result["handler_function_name"] and not result["tool_name"]:
        # Try to infer from handler name (e.g., "life_search_handler" -> "life_search")
        handler_name = result["handler_function_name"]
        if handler_name.endswith("_handler") or handler_name.endswith("_tool"):
            result["tool_name"] = handler_name.rsplit("_", 1)[0]
        else:
            result["tool_name"] = handler_name
    
    # If we have enough info, return it
    if result["tool_name"] and result["handler_function_name"] and result["tool_file_code"]:
        return result
    
    return None


def create_tool_file(tool_name: str, tool_code: str) -> bool:
    """Create the tool file in mcp_tools/ directory"""
    try:
        mcp_tools_dir = Path("mcp_tools")
        mcp_tools_dir.mkdir(exist_ok=True)
        
        tool_file = mcp_tools_dir / f"{tool_name}.py"
        
        # Write the tool file
        with open(tool_file, 'w', encoding='utf-8') as f:
            f.write(tool_code)
        
        return True
    except Exception as e:
        print(f"Error creating tool file: {e}")
        return False


def update_init_file(tool_name: str, handler_function_name: str) -> bool:
    """Update mcp_tools/__init__.py to export the tool"""
    try:
        init_file = Path("mcp_tools/__init__.py")
        
        # Read existing content
        if init_file.exists():
            with open(init_file, 'r') as f:
                content = f.read()
        else:
            content = '"""\nMCP Tools Module\n"""\n\n__all__ = []\n'
        
        # Check if already imported
        import_line = f"from .{tool_name} import {handler_function_name}"
        if import_line in content:
            return True  # Already there
        
        # Add import before __all__
        if "__all__" in content:
            lines = content.split('\n')
            all_index = None
            for i, line in enumerate(lines):
                if '__all__' in line and '=' in line:
                    all_index = i
                    break
            
            if all_index is not None:
                # Insert import before __all__
                lines.insert(all_index, import_line)
                
                # Update __all__ list
                for i, line in enumerate(lines):
                    if '__all__' in line and '=' in line and '[' in line:
                        # Extract existing items
                        all_start = line.find('[')
                        all_end = line.find(']')
                        if all_start >= 0 and all_end > all_start:
                            all_content = line[all_start+1:all_end].strip()
                            if all_content:
                                # Parse existing items
                                items = [item.strip().strip("'\"") for item in all_content.split(',') if item.strip()]
                            else:
                                items = []
                            
                            # Add new item if not already there
                            if handler_function_name not in items:
                                items.append(handler_function_name)
                            
                            # Rebuild __all__ line
                            items_str = ', '.join([f"'{item}'" for item in items])
                            lines[i] = f"__all__ = [{items_str}]"
                        break
                
                content = '\n'.join(lines)
            else:
                content += f"\n{import_line}\n"
        else:
            content += f"\n{import_line}\n__all__ = ['{handler_function_name}']\n"
        
        # Write back
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Error updating __init__.py: {e}")
        return False


def update_server_file(tool_name: str, handler_function_name: str, description: str, parameters: dict) -> bool:
    """Update local_mcp_server.py to register the tool"""
    try:
        server_file = Path("local_mcp_server.py")
        
        if not server_file.exists():
            return False
        
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already registered
        if f'name="{tool_name}"' in content or f"name='{tool_name}'" in content:
            return True  # Already registered
        
        # Find insertion point (after web_search tool registration, before mcp_tools loading)
        insert_marker = "# Load custom tools from mcp_tools directory"
        
        if insert_marker in content:
            lines = content.split('\n')
            marker_index = next((i for i, line in enumerate(lines) if insert_marker in line), None)
            
            if marker_index is not None:
                # Build registration code
                params_json = json.dumps(parameters, indent=8)
                
                registration_code = f"""
# Register {tool_name} tool
try:
    from mcp_tools import {handler_function_name}
    register_tool(
        name="{tool_name}",
        description="{description}",
        parameters={params_json},
        handler={handler_function_name}
    )
except ImportError:
    # Tool not available
    pass
"""
                
                lines.insert(marker_index, registration_code.strip())
                content = '\n'.join(lines)
            else:
                # Fallback: add before if __name__ == "__main__"
                if 'if __name__' in content:
                    lines = content.split('\n')
                    main_index = next((i for i, line in enumerate(lines) if '__name__' in line), None)
                    if main_index:
                        params_json = json.dumps(parameters, indent=8)
                        registration_code = f"""
# Register {tool_name} tool
try:
    from mcp_tools import {handler_function_name}
    register_tool(
        name="{tool_name}",
        description="{description}",
        parameters={params_json},
        handler={handler_function_name}
    )
except ImportError:
    pass

"""
                        lines.insert(main_index, registration_code.strip())
                        content = '\n'.join(lines)
        
        # Write back
        with open(server_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Error updating local_mcp_server.py: {e}")
        return False


def create_tool_from_response(response: str) -> Tuple[bool, str]:
    """
    Parse Tool Builder response and create tool files automatically
    
    Returns:
        (success: bool, message: str)
    """
    tool_info = extract_tool_code_from_response(response)
    
    if not tool_info:
        return False, "Could not extract tool information from response"
    
    tool_name = tool_info["tool_name"]
    handler_function_name = tool_info["handler_function_name"]
    tool_code = tool_info["tool_file_code"]
    
    if not tool_name or not handler_function_name or not tool_code:
        return False, f"Missing required information. Found: tool_name={tool_name}, handler={handler_function_name}, code={'yes' if tool_code else 'no'}"
    
    # Check if tool file already exists
    tool_file_path = Path(f"mcp_tools/{tool_name}.py")
    if tool_file_path.exists():
        return False, f"Tool file mcp_tools/{tool_name}.py already exists. Delete it first if you want to recreate it."
    
    # Create tool file
    if not create_tool_file(tool_name, tool_code):
        return False, f"Failed to create mcp_tools/{tool_name}.py"
    
    # Update __init__.py
    if not update_init_file(tool_name, handler_function_name):
        return False, f"Failed to update mcp_tools/__init__.py"
    
    # Update server file
    description = tool_info.get("description", f"{tool_name} tool")
    parameters = tool_info.get("parameters", {})
    
    # If parameters dict is empty or invalid, create a basic one
    if not parameters or not isinstance(parameters, dict):
        # Try to extract parameters from the code
        params_match = re.search(r'arguments\.get\(["\'](\w+)["\']', tool_code)
        if params_match:
            param_name = params_match.group(1)
            parameters = {
                param_name: {
                    "type": "string",
                    "description": f"The {param_name} parameter"
                }
            }
        else:
            # Default parameter
            parameters = {
                "query": {
                    "type": "string",
                    "description": "Search query or input"
                }
            }
    
    if not update_server_file(tool_name, handler_function_name, description, parameters):
        return False, f"Failed to update local_mcp_server.py"
    
    return True, f"✅ Tool '{tool_name}' created successfully!\n\nFiles created:\n- mcp_tools/{tool_name}.py\n- Updated mcp_tools/__init__.py\n- Updated local_mcp_server.py\n\n🔄 Please restart the MCP server to use the new tool."
