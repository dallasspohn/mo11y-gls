# Tool Builder Testing Guide

## Simple Test Tasks

When testing the Tool Builder persona, start with simple tasks to avoid high CPU usage or lockups.

### ✅ Recommended Simple Tasks

#### 1. File Reader Tool (Simplest)
**Ask**: "Create a tool that reads a text file and returns its contents"

**Why it's good**:
- Simple file I/O
- No heavy processing
- Quick execution
- Useful functionality

#### 2. Text Case Converter
**Ask**: "Create a tool that converts text to uppercase or lowercase"

**Why it's good**:
- Very simple string operations
- No file I/O
- Instant results
- Easy to test

#### 3. Current Date/Time Tool
**Ask**: "Create a tool that returns the current date and time"

**Why it's good**:
- Single function call
- No processing
- Instant response
- Useful utility

#### 4. Directory Lister
**Ask**: "Create a tool that lists files in a directory"

**Why it's good**:
- Simple directory operation
- No heavy processing
- Useful for file management
- Quick execution

#### 5. Word Counter
**Ask**: "Create a tool that counts words in a text string"

**Why it's good**:
- Simple string processing
- No file I/O needed
- Quick calculation
- Easy to verify

### ❌ Avoid These (Too Complex/Heavy)

- **Network scanners** - High CPU, network I/O, can lock up
- **Web scrapers** - Network delays, parsing overhead
- **Image processors** - Heavy CPU/memory usage
- **Database queries** - Can be slow, requires setup
- **Large file processors** - Memory intensive
- **Recursive operations** - Can cause loops

## Testing Workflow

1. **Start Simple**: Begin with file reader or text converter
2. **Test Incrementally**: Add complexity gradually
3. **Monitor Resources**: Watch CPU/memory usage
4. **Test Each Tool**: Verify it works before moving on

## Example Test Session

```
You: "Create a tool that reads a text file and returns its contents"

Tool Builder will:
1. Design the tool interface
2. Generate handler function
3. Show registration code
4. Provide test command

You: Test it
Tool Builder: Shows how to test via MCP client

You: "Now add error handling for file not found"
Tool Builder: Updates the code with try/except
```

## Quick Test Commands

After Tool Builder generates code, test with:

```bash
# Start MCP server (if not running)
python3 local_mcp_server.py

# In another terminal, test the tool
python3 -c "
from mcp_connection import MCPClient
client = MCPClient(mcp_server_url='http://localhost:8443')
result = client.call_tool('your_tool_name', {'param': 'value'})
print(result)
"
```

## Tips

- **Start with file operations** - Simple and useful
- **Avoid network tools initially** - Can cause delays
- **Test one tool at a time** - Easier to debug
- **Check MCP server logs** - See if tool is being called
- **Use simple parameters** - Avoid complex data structures

## Recommended First Tool

**File Reader** is the best first tool because:
- ✅ Simple to understand
- ✅ Quick to execute
- ✅ Useful functionality
- ✅ Easy to test
- ✅ No heavy processing
- ✅ Demonstrates file I/O pattern

Ask Tool Builder: **"Create a tool that reads a text file and returns its contents"**
