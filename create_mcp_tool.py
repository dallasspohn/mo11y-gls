#!/usr/bin/env python3
"""
Helper script to create MCP tools
Usage: python3 create_mcp_tool.py <tool_name> <description>
"""

import sys
import os
import json
from pathlib import Path

def create_tool_file(tool_name: str, handler_code: str, description: str):
    """Create a tool file in mcp_tools/ directory"""
    mcp_tools_dir = Path("mcp_tools")
    mcp_tools_dir.mkdir(exist_ok=True)
    
    tool_file = mcp_tools_dir / f"{tool_name}.py"
    
    # Write the tool file
    with open(tool_file, 'w') as f:
        f.write(handler_code)
    
    print(f"✅ Created: {tool_file}")
    return tool_file

def update_init_file(tool_name: str, handler_function_name: str):
    """Update mcp_tools/__init__.py to export the tool"""
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
        print(f"⚠️  {handler_function_name} already in __init__.py")
        return
    
    # Add import before __all__
    if "__all__" in content:
        # Insert before __all__
        lines = content.split('\n')
        all_index = next(i for i, line in enumerate(lines) if '__all__' in line)
        lines.insert(all_index, import_line)
        
        # Update __all__ list
        for i, line in enumerate(lines):
            if '__all__' in line and '=' in line:
                # Extract existing __all__ items
                if '[' in line and ']' in line:
                    all_start = line.find('[')
                    all_end = line.find(']')
                    all_content = line[all_start+1:all_end].strip()
                    if all_content:
                        items = [item.strip().strip("'\"") for item in all_content.split(',')]
                    else:
                        items = []
                    items.append(f"'{handler_function_name}'")
                    lines[i] = f"__all__ = [{', '.join([f\"'{item}'\" for item in items])}]"
                else:
                    lines[i] = f"__all__ = ['{handler_function_name}']"
                break
        
        content = '\n'.join(lines)
    else:
        # Add at end
        content += f"\n{import_line}\n__all__ = ['{handler_function_name}']\n"
    
    # Write back
    with open(init_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated: {init_file}")

def update_server_file(tool_name: str, handler_function_name: str, description: str, parameters: dict):
    """Update local_mcp_server.py to register the tool"""
    server_file = Path("local_mcp_server.py")
    
    if not server_file.exists():
        print(f"❌ {server_file} not found")
        return
    
    with open(server_file, 'r') as f:
        content = f.read()
    
    # Check if already registered
    if f'name="{tool_name}"' in content:
        print(f"⚠️  Tool '{tool_name}' already registered in local_mcp_server.py")
        return
    
    # Find where to insert (after web_search tool registration)
    insert_marker = "# Load custom tools from mcp_tools directory"
    
    if insert_marker in content:
        # Insert before the mcp_tools loading section
        lines = content.split('\n')
        marker_index = next(i for i, line in enumerate(lines) if insert_marker in line)
        
        # Build registration code
        params_str = json.dumps(parameters, indent=16).replace('"', '')
        params_str = params_str.replace('{', '{').replace('}', '}')
        
        registration_code = f"""
# Register {tool_name} tool
try:
    from mcp_tools import {handler_function_name}
    register_tool(
        name="{tool_name}",
        description="{description}",
        parameters={json.dumps(parameters, indent=8)},
        handler={handler_function_name}
    )
except ImportError:
    # Tool not available
    pass
"""
        
        lines.insert(marker_index, registration_code.strip())
        content = '\n'.join(lines)
    else:
        # Add at end before if __name__ == "__main__"
        if 'if __name__' in content:
            lines = content.split('\n')
            main_index = next(i for i, line in enumerate(lines) if '__name__' in line)
            
            registration_code = f"""
# Register {tool_name} tool
try:
    from mcp_tools import {handler_function_name}
    register_tool(
        name="{tool_name}",
        description="{description}",
        parameters={json.dumps(parameters, indent=8)},
        handler={handler_function_name}
    )
except ImportError:
    pass

"""
            lines.insert(main_index, registration_code.strip())
            content = '\n'.join(lines)
    
    with open(server_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated: {server_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 create_mcp_tool.py <tool_name>")
        print("\nThis script helps create MCP tools.")
        print("Tool Builder will provide the code, and you can use this script to apply it.")
        sys.exit(1)
    
    print("Tool creation helper script")
    print("Tool Builder will provide the code - this script helps apply it.")
    print("\nFor now, manually create the files as Tool Builder instructs.")
    print("Future versions may automate this process.")
