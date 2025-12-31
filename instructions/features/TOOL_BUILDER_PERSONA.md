# Tool Builder Persona Guide

## Overview

The **Tool Builder** persona is a specialized AI assistant focused on creating, testing, and managing MCP (Model Context Protocol) tools. It's designed to help you extend Mo11y's capabilities by building custom tools.

## Features

✅ **Tool Creation**: Design and implement new MCP tools  
✅ **Tool Management**: Modify, debug, and optimize existing tools  
✅ **Code Generation**: Generate complete, working Python code  
✅ **MCP Expertise**: Deep understanding of MCP protocol and JSON-RPC 2.0  
✅ **Testing Support**: Provides test examples and debugging help  

## How to Use

### 1. Select the Persona

In the Streamlit app sidebar, select **"Tool Builder"** from the persona dropdown.

### 2. Change the Model (Optional)

Edit `sonas/tool-builder.json` and change the `model_name` field:

```json
{
  "model_name": "your-preferred-model:latest"
}
```

Current default: `deepseek-r1:latest`

### 3. Start Creating Tools

Simply describe what you want the tool to do:

**Example:**
```
You: "I want a tool that reads a file and returns its contents"

Tool Builder will:
1. Design the tool interface
2. Generate complete Python code
3. Show where to add it in local_mcp_server.py
4. Provide test examples
```

## What Tool Builder Can Help With

### Creating New Tools
- File operations (read, write, list files)
- API integrations
- Data processing
- Web scraping
- Database operations
- System commands (safely)
- Custom business logic

### Modifying Existing Tools
- Adding error handling
- Improving performance
- Adding new parameters
- Fixing bugs
- Optimizing code

### Debugging
- Tool not working? Tool Builder will help debug
- Error messages? Get systematic troubleshooting
- Performance issues? Get optimization suggestions

## MCP Tool Structure

Tool Builder understands the MCP tool structure:

1. **Handler Function**: Python function that does the work
2. **Tool Registration**: Registers the tool with the MCP server
3. **JSON-RPC Format**: Proper response format

## Example Workflow

```
You: "Create a tool that searches for text in files"

Tool Builder:
1. Asks clarifying questions (which directory? recursive?)
2. Designs the tool interface
3. Generates code:
   - Handler function
   - Registration code
   - Error handling
4. Shows where to add it
5. Provides test command
```

## Requirements

- MCP server must be running (`python3 local_mcp_server.py`)
- Access to `local_mcp_server.py` file for modifications
- Python knowledge helpful but not required (Tool Builder explains everything)

## Tips

1. **Be Specific**: The more details you provide, the better the tool
2. **Ask Questions**: Tool Builder will ask clarifying questions if needed
3. **Test Incrementally**: Test tools as you build them
4. **Review Code**: Tool Builder generates code - review it before using

## Next Steps

1. Select "Tool Builder" persona in the app
2. Describe your tool idea
3. Follow the generated instructions
4. Test your new tool!

Happy tool building! 🛠️
