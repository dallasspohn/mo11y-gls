"""
MCP (Model Context Protocol) Server Integration
Integrates with docker-mcp server for enhanced capabilities
"""

import json
import subprocess
from typing import Dict, List, Optional
from datetime import datetime

from mcp_connection import MCPClient


class MCPToolExecutor:
    """
    Executes MCP tools in the context of Mo11y agent
    Integrates MCP tools with agent workflow
    """
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.tool_history = []
    
    def execute_tool(self, tool_name: str, arguments: Dict, context: Dict = None) -> Dict:
        """
        Execute an MCP tool with context
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            context: Additional context from agent
        
        Returns:
            Execution result with success status and output
        """
        # Get tool definition
        tool_def = self.mcp_client.get_tool(tool_name)
        if not tool_def:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "output": None
            }
        
        # Merge context into arguments if needed
        if context:
            arguments = {**arguments, **context}
        
        # Execute tool
        try:
            result = self.mcp_client.call_tool(tool_name, arguments)
            
            # Log execution
            self.tool_history.append({
                "tool": tool_name,
                "arguments": arguments,
                "timestamp": datetime.now().isoformat(),
                "success": result is not None
            })
            
            if result:
                # Handle different result formats
                output = result
                if isinstance(result, dict):
                    # Check for content field (MCP format)
                    if "content" in result:
                        content = result["content"]
                        # If content is a list, get first item
                        if isinstance(content, list) and len(content) > 0:
                            content = content[0]
                        # If content is dict, extract values
                        if isinstance(content, dict):
                            output = content
                        else:
                            output = content
                    # Check for direct fields (like image_path from our tool)
                    elif "image_path" in result:
                        output = result
                    else:
                        output = result
                
                # Return result with all fields preserved
                return {
                    "success": True,
                    "output": output,
                    "isError": result.get("isError", False) if isinstance(result, dict) else False,
                    # Preserve all fields from result (like image_path)
                    **({k: v for k, v in result.items() if isinstance(result, dict)})
                }
            else:
                return {
                    "success": False,
                    "error": "Tool execution returned no result",
                    "output": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": None
            }
    
    def get_available_tools_summary(self) -> str:
        """Get a summary of available tools for LLM context"""
        tools = self.mcp_client.list_tools()
        
        if not tools:
            return "No MCP tools available."
        
        summary = "Available MCP Tools:\n"
        for tool in tools:
            summary += f"- {tool['name']}: {tool.get('description', 'No description')}\n"
            if 'inputSchema' in tool:
                params = tool['inputSchema'].get('properties', {})
                if params:
                    summary += "  Parameters:\n"
                    for param_name, param_def in params.items():
                        summary += f"    - {param_name}: {param_def.get('description', '')}\n"
        
        return summary
    
    def suggest_tool_for_query(self, user_query: str) -> Optional[str]:
        """
        Suggest which tool to use based on user query
        
        Args:
            user_query: User's query/text
        
        Returns:
            Suggested tool name or None
        """
        tools = self.mcp_client.list_tools()
        query_lower = user_query.lower()
        
        # Simple keyword matching (can be enhanced with embeddings)
        for tool in tools:
            tool_name = tool['name'].lower()
            description = tool.get('description', '').lower()
            
            # Check if query keywords match tool
            if any(keyword in tool_name or keyword in description 
                   for keyword in query_lower.split() if len(keyword) > 3):
                return tool['name']
        
        return None


# Docker MCP Server Helper
class DockerMCPServer:
    """
    Helper for managing docker-mcp server
    Handles docker container lifecycle and connection
    """
    
    @staticmethod
    def check_docker_mcp_running(container_name: str = "docker-mcp") -> bool:
        """Check if docker-mcp container is running"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return container_name in result.stdout
        except:
            return False
    
    @staticmethod
    def start_docker_mcp(container_name: str = "docker-mcp", 
                        image: str = "docker-mcp:latest") -> bool:
        """Start docker-mcp container"""
        try:
            # Check if already running
            if DockerMCPServer.check_docker_mcp_running(container_name):
                return True
            
            # Start container
            result = subprocess.run(
                ["docker", "start", container_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True
            
            # Try to run new container
            result = subprocess.run(
                ["docker", "run", "-d", "--name", container_name, image],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.returncode == 0
            
        except Exception as e:
            return False
    
    @staticmethod
    def get_docker_mcp_url(container_name: str = "docker-mcp", 
                          port: int = 3000) -> Optional[str]:
        """Get URL for docker-mcp server"""
        if DockerMCPServer.check_docker_mcp_running(container_name):
            # Try to get container IP or use localhost
            try:
                result = subprocess.run(
                    ["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", container_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                ip = result.stdout.strip()
                if ip:
                    return f"http://{ip}:{port}"
            except:
                pass
            
            return f"http://localhost:{port}"
        
        return None
