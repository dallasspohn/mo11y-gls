#!/usr/bin/env python3
"""
Local MCP Server using LangGraph, Ollama, and FastAPI
Compatible with existing MCP client code
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import os
from datetime import datetime

# Try to import LangGraph (optional)
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("Warning: LangGraph not available. Install with: pip install langgraph")

# Try to import Ollama
try:
    from ollama import chat, list as ollama_list
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("Warning: Ollama not available. Install with: pip install ollama")

# Try to import DuckDuckGo for web search
try:
    from duckduckgo_search import DDGS
    DDG_AVAILABLE = True
except ImportError:
    DDG_AVAILABLE = False
    print("Warning: DuckDuckGo search not available. Install with: pip install duckduckgo-search")

app = FastAPI(title="Local MCP Server")

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JSON-RPC 2.0 Request/Response models
class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    method: str
    params: Optional[Dict] = None

class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    result: Optional[Any] = None
    error: Optional[Dict] = None

# Tool registry
TOOLS = {}
RESOURCES = {}
PROMPTS = {}

def register_tool(name: str, description: str, parameters: Dict, handler: callable):
    """Register a tool with the MCP server"""
    TOOLS[name] = {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": parameters,
            "required": list(parameters.keys())
        },
        "handler": handler
    }

def register_resource(uri: str, name: str, description: str, mime_type: str = "text/plain"):
    """Register a resource with the MCP server"""
    RESOURCES[uri] = {
        "uri": uri,
        "name": name,
        "description": description,
        "mimeType": mime_type
    }

def register_prompt(name: str, description: str, arguments: List[str], template: str):
    """Register a prompt template"""
    PROMPTS[name] = {
        "name": name,
        "description": description,
        "arguments": arguments,
        "template": template
    }

# Example tools
def example_echo_tool(arguments: Dict) -> Dict:
    """Echo tool - returns what you send it"""
    text = arguments.get("text", "")
    return {
        "content": [
            {
                "type": "text",
                "text": f"Echo: {text}"
            }
        ],
        "isError": False
    }

def example_calculator_tool(arguments: Dict) -> Dict:
    """Simple calculator tool"""
    try:
        expression = arguments.get("expression", "")
        result = eval(expression)  # In production, use a safe evaluator
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Result: {result}"
                }
            ],
            "isError": False
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: {str(e)}"
                }
            ],
            "isError": True
        }

def example_ollama_chat_tool(arguments: Dict) -> Dict:
    """Chat with Ollama"""
    if not OLLAMA_AVAILABLE:
        return {
            "content": [{"type": "text", "text": "Ollama not available"}],
            "isError": True
        }
    
    model = arguments.get("model", "deepseek-r1:latest")
    message = arguments.get("message", "")
    
    try:
        response = chat(
            model=model,
            messages=[{"role": "user", "content": message}]
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": response.get("message", {}).get("content", "")
                }
            ],
            "isError": False
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }

def web_search_tool(arguments: Dict) -> Dict:
    """Search the web using DuckDuckGo"""
    if not DDG_AVAILABLE:
        return {
            "content": [{"type": "text", "text": "DuckDuckGo search not available. Install with: pip install duckduckgo-search"}],
            "isError": True
        }
    
    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 5)
    
    if not query:
        return {
            "content": [{"type": "text", "text": "Error: 'query' parameter is required"}],
            "isError": True
        }
    
    try:
        with DDGS() as ddgs:
            results = []
            for result in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", "")
                })
            
            # Format results as text
            formatted_results = f"Web Search Results for: {query}\n\n"
            for i, result in enumerate(results, 1):
                formatted_results += f"{i}. {result['title']}\n"
                formatted_results += f"   URL: {result['url']}\n"
                formatted_results += f"   {result['snippet']}\n\n"
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": formatted_results
                    }
                ],
                "isError": False
            }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Search error: {str(e)}"}],
            "isError": True
        }

# Register example tools
register_tool(
    name="echo",
    description="Echo back the text you send",
    parameters={
        "text": {
            "type": "string",
            "description": "Text to echo back"
        }
    },
    handler=example_echo_tool
)

register_tool(
    name="calculator",
    description="Evaluate a mathematical expression",
    parameters={
        "expression": {
            "type": "string",
            "description": "Mathematical expression to evaluate (e.g., '2 + 2')"
        }
    },
    handler=example_calculator_tool
)

if OLLAMA_AVAILABLE:
    register_tool(
        name="ollama_chat",
        description="Chat with an Ollama model",
        parameters={
            "model": {
                "type": "string",
                "description": "Ollama model name (e.g., 'deepseek-r1:latest')"
            },
            "message": {
                "type": "string",
                "description": "Message to send to the model"
            }
        },
        handler=example_ollama_chat_tool
    )
    
    # Add Ollama management tools
    def ollama_list_models_tool(arguments: Dict) -> Dict:
        """List available Ollama models"""
        try:
            models_response = ollama_list()
            models_list = []
            if isinstance(models_response, dict):
                models_list = models_response.get("models", [])
            elif isinstance(models_response, list):
                models_list = models_response
            
            model_names = []
            for m in models_list:
                if isinstance(m, dict):
                    name = m.get("name") or m.get("model", "")
                elif isinstance(m, str):
                    name = m
                else:
                    name = str(m)
                if name:
                    model_names.append(name)
            
            if not model_names:
                return {
                    "content": [{"type": "text", "text": "No models found. Use 'ollama pull <model-name>' to download models."}],
                    "isError": False
                }
            
            return {
                "content": [{"type": "text", "text": f"Available Ollama models:\n" + "\n".join(f"  - {name}" for name in model_names)}],
                "isError": False
            }
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"Error listing models: {str(e)}"}],
                "isError": True
            }
    
    def ollama_pull_model_tool(arguments: Dict) -> Dict:
        """Pull/download an Ollama model"""
        try:
            import subprocess
            model_name = arguments.get("model", "")
            if not model_name:
                return {
                    "content": [{"type": "text", "text": "Error: 'model' parameter is required (e.g., 'deepseek-r1:latest')"}],
                    "isError": True
                }
            
            # Use subprocess to call ollama pull
            result = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout for large models
            )
            
            if result.returncode == 0:
                return {
                    "content": [{"type": "text", "text": f"Successfully pulled model: {model_name}\n{result.stdout}"}],
                    "isError": False
                }
            else:
                return {
                    "content": [{"type": "text", "text": f"Error pulling model: {result.stderr or result.stdout}"}],
                    "isError": True
                }
        except subprocess.TimeoutExpired:
            return {
                "content": [{"type": "text", "text": f"Timeout: Model pull is taking too long. This is normal for large models. Check progress with: ollama list"}],
                "isError": True
            }
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }
    
    register_tool(
        name="ollama_list_models",
        description="List all available Ollama models",
        parameters={},
        handler=ollama_list_models_tool
    )
    
    register_tool(
        name="ollama_pull_model",
        description="Pull/download an Ollama model (e.g., 'deepseek-r1:latest')",
        parameters={
            "model": {
                "type": "string",
                "description": "Model name to pull (e.g., 'deepseek-r1:latest', 'llama3.2:3b')"
            }
        },
        handler=ollama_pull_model_tool
    )

# Register web search tool
register_tool(
    name="web_search",
    description="Search the web using DuckDuckGo. Returns search results with titles, URLs, and snippets. Supports site-specific searches using 'site:domain.com' syntax (e.g., 'site:spohnz.com' to search only that website).",
    parameters={
        "query": {
            "type": "string",
            "description": "Search query"
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results to return (default: 5)",
            "default": 5
        }
    },
    handler=web_search_tool
)

# Register Red Hat content creation tool
try:
    from redhat_content_creator import RedHatContentCreator
    REDHAT_CONTENT_AVAILABLE = True
    
    # Initialize content creator with auto-pull enabled
    # Configuration can be loaded from config.json or environment variables
    import json
    import os
    
    # Try to load config
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    redhat_config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                redhat_config = config.get("redhat_content", {})
        except:
            pass
    
    # Get settings from config or use defaults
    standards_dir = redhat_config.get("standards_dir", "/home/dallas/dev/redhat-content-standards")
    standards_repo = redhat_config.get("standards_repo") or os.getenv("REDHAT_STANDARDS_REPO")
    auto_pull = redhat_config.get("auto_pull", True)
    
    _content_creator = RedHatContentCreator(
        standards_dir=standards_dir,
        standards_repo=standards_repo,
        auto_pull=auto_pull
    )
    
    def create_redhat_content_tool(arguments: Dict) -> Dict:
        """Create Red Hat training content (lectures, GEs, lab scripts)"""
        try:
            user_request = arguments.get("request", "")
            output_dir = arguments.get("output_directory", "/home/dallas/dev/au0025l-demo")
            
            # Parse the request
            parsed = _content_creator.parse_content_request(user_request)
            
            # Create all requested content
            results = _content_creator.create_all_content(
                topic=parsed["topic"],
                output_dir=output_dir,
                course_id=parsed["course_id"],
                content_types=parsed["content_types"]
            )
            
            # Format results
            result_text = f"Created Red Hat content for '{parsed['topic']}':\n\n"
            result_text += f"Content Types: {', '.join(parsed['content_types'])}\n"
            result_text += f"Output Directory: {output_dir}\n"
            result_text += f"Course ID: {parsed['course_id']}\n\n"
            result_text += "Files Created:\n"
            
            for content_type, paths in results.items():
                if isinstance(paths, dict):
                    result_text += f"\n{content_type.upper()}:\n"
                    for key, path in paths.items():
                        result_text += f"  - {key}: {path}\n"
                else:
                    result_text += f"  - {content_type}: {paths}\n"
            
            return {
                "content": [{"type": "text", "text": result_text}],
                "isError": False,
                "files_created": results,
                "parsed_request": parsed
            }
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"Error creating Red Hat content: {str(e)}"}],
                "isError": True
            }
    
    register_tool(
        name="create_redhat_content",
        description="Create Red Hat training content including lectures, Guided Exercises (GEs), and lab scripts (dynolabs). Parses natural language requests like 'create a lecture and GE on Ansible Roles' and generates all required files following Red Hat content standards.",
        parameters={
            "request": {
                "type": "string",
                "description": "Natural language request describing what content to create (e.g., 'create a lecture and GE on Ansible Roles Create in /home/dallas/dev/au0025l-demo')"
            },
            "output_directory": {
                "type": "string",
                "description": "Output directory for created content (default: /home/dallas/dev/au0025l-demo)",
                "default": "/home/dallas/dev/au0025l-demo"
            }
        },
        handler=create_redhat_content_tool
    )
except ImportError:
    REDHAT_CONTENT_AVAILABLE = False
    print("Warning: Red Hat content creator not available")

# Load custom tools from mcp_tools directory
try:
    import sys
    import os
    mcp_tools_dir = os.path.join(os.path.dirname(__file__), "mcp_tools")
    if os.path.exists(mcp_tools_dir):
        # Add mcp_tools to path if not already there
        if mcp_tools_dir not in sys.path:
            sys.path.insert(0, os.path.dirname(__file__))
        
        # Try to import and register tools from mcp_tools
        try:
            from mcp_tools import file_reader_tool
            register_tool(
                name="file_reader",
                description="Reads a text file and returns its contents",
                parameters={
                    "filename": {
                        "type": "string",
                        "description": "Path to the text file to be read"
                    }
                },
                handler=file_reader_tool
            )
        except ImportError:
            # mcp_tools module not available or file_reader not defined - that's okay
            pass
        
        try:
            from mcp_tools import textcase_handler
            register_tool(
                name="textcase",
                description="Converts text to uppercase or lowercase",
                parameters={
                    "text": {
                        "type": "string",
                        "description": "The input text to be converted"
                    },
                    "mode": {
                        "type": "string",
                        "description": "Conversion mode: 'uppercase' or 'lowercase' (default: lowercase)"
                    }
                },
                handler=textcase_handler
            )
        except ImportError:
            pass
        
        try:
            from mcp_tools import generate_image_tool, IMAGE_GENERATOR_METADATA
            register_tool(
                name="generate_image",
                description=IMAGE_GENERATOR_METADATA["description"],
                parameters=IMAGE_GENERATOR_METADATA["inputSchema"]["properties"],
                handler=generate_image_tool
            )
        except ImportError:
            pass
except Exception as e:
    # Silently fail if mcp_tools can't be loaded
    pass

# Register example resources
register_resource(
    uri="local://server-info",
    name="Server Information",
    description="Information about this MCP server"
)

register_resource(
    uri="local://tools-list",
    name="Available Tools",
    description="List of all available tools"
)

# Register example prompts
register_prompt(
    name="greeting",
    description="Generate a greeting",
    arguments=["name"],
    template="Hello, {name}! How can I help you today?"
)

@app.post("/")
async def handle_jsonrpc(request: JSONRPCRequest):
    """Handle JSON-RPC 2.0 requests"""
    try:
        result = await process_mcp_method(request.method, request.params or {})
        return JSONRPCResponse(
            jsonrpc="2.0",
            id=request.id,
            result=result
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"MCP Server Error: {str(e)}")
        print(f"Traceback: {error_trace}")
        return JSONRPCResponse(
            jsonrpc="2.0",
            id=request.id,
            error={
                "code": -32000,
                "message": str(e)
            }
        )

async def process_mcp_method(method: str, params: Dict) -> Any:
    """Process MCP protocol methods"""
    
    # Initialize
    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True}
            },
            "serverInfo": {
                "name": "local-mcp-server",
                "version": "1.0.0"
            }
        }
    
    # Tools
    elif method == "tools/list":
        tools_list = []
        for name, tool in TOOLS.items():
            # Create a copy without the handler function
            tool_def = {
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": tool["inputSchema"]
            }
            tools_list.append(tool_def)
        return {
            "tools": tools_list
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in TOOLS:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        handler = TOOLS[tool_name]["handler"]
        result = handler(arguments)
        return result
    
    # Resources
    elif method == "resources/list":
        resources_list = []
        for uri, res in RESOURCES.items():
            # Create a copy without any handler functions
            resource_def = {
                "uri": res["uri"],
                "name": res["name"],
                "description": res["description"],
                "mimeType": res.get("mimeType", "text/plain")
            }
            resources_list.append(resource_def)
        return {
            "resources": resources_list
        }
    
    elif method == "resources/read":
        uri = params.get("uri")
        
        if uri == "local://server-info":
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "text/plain",
                        "text": json.dumps({
                            "name": "local-mcp-server",
                            "version": "1.0.0",
                            "tools_count": len(TOOLS),
                            "resources_count": len(RESOURCES),
                            "langgraph_available": LANGGRAPH_AVAILABLE,
                            "ollama_available": OLLAMA_AVAILABLE
                        }, indent=2)
                    }
                ]
            }
        elif uri == "local://tools-list":
            tools_list = [
                {
                    "name": tool["name"],
                    "description": tool["description"]
                }
                for tool in TOOLS.values()
            ]
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(tools_list, indent=2)
                    }
                ]
            }
        elif uri in RESOURCES:
            # Return resource content
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": RESOURCES[uri].get("mimeType", "text/plain"),
                        "text": f"Resource: {RESOURCES[uri]['name']}"
                    }
                ]
            }
        else:
            raise ValueError(f"Resource '{uri}' not found")
    
    # Prompts
    elif method == "prompts/list":
        prompts_list = []
        for name, prompt in PROMPTS.items():
            # Create a copy without the template
            prompt_def = {
                "name": prompt["name"],
                "description": prompt["description"],
                "arguments": prompt["arguments"]
            }
            prompts_list.append(prompt_def)
        return {
            "prompts": prompts_list
        }
    
    elif method == "prompts/get":
        prompt_name = params.get("name")
        prompt_args = params.get("arguments", {})
        
        if prompt_name not in PROMPTS:
            raise ValueError(f"Prompt '{prompt_name}' not found")
        
        prompt = PROMPTS[prompt_name]
        template = prompt["template"]
        
        # Format template with arguments
        try:
            formatted = template.format(**prompt_args)
        except KeyError as e:
            raise ValueError(f"Missing required argument: {e}")
        
        return {
            "messages": [
                {
                    "role": "user",
                    "content": formatted
                }
            ]
        }
    
    else:
        raise ValueError(f"Unknown method: {method}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "tools": len(TOOLS),
        "resources": len(RESOURCES),
        "prompts": len(PROMPTS)
    }

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable or use default 8443
    mcp_port = int(os.getenv("MCP_SERVER_PORT", "8443"))
    
    print("🚀 Starting Local MCP Server...")
    print(f"   LangGraph available: {LANGGRAPH_AVAILABLE}")
    print(f"   Ollama available: {OLLAMA_AVAILABLE}")
    print(f"   DuckDuckGo search available: {DDG_AVAILABLE}")
    print(f"   Tools registered: {len(TOOLS)}")
    print(f"   Resources registered: {len(RESOURCES)}")
    print(f"   Prompts registered: {len(PROMPTS)}")
    print(f"\n📡 Server will be available at: http://localhost:{mcp_port}")
    print(f"   Use this URL in your config.json: http://localhost:{mcp_port}")
    print(f"   Or set MCP_SERVER_PORT environment variable to change port")
    print("\n🔍 Available tools:")
    for tool_name in TOOLS.keys():
        print(f"   - {tool_name}")
    
    uvicorn.run(app, host="0.0.0.0", port=mcp_port)
