"""
MCP (Model Context Protocol) Connection Client
Handles connection and communication with MCP servers
"""

import json
import subprocess
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests


class MCPClient:
    """
    Client for interacting with MCP (Model Context Protocol) servers
    Supports docker-mcp server integration
    """
    
    def __init__(self, mcp_server_url: str = None, mcp_server_path: str = None):
        """
        Initialize MCP client
        
        Args:
            mcp_server_url: URL of MCP server (if HTTP-based)
            mcp_server_path: Path to docker-mcp server or command
        """
        self.mcp_server_url = mcp_server_url
        self.mcp_server_path = mcp_server_path or os.getenv("MCP_SERVER_PATH")
        self.tools_cache = {}
        self.resources_cache = {}
        self.last_sync = None
    
    def _call_mcp_server(self, method: str, params: Dict = None) -> Optional[Dict]:
        """
        Call MCP server using JSON-RPC protocol
        
        MCP uses JSON-RPC 2.0 protocol:
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "method_name",
            "params": {...}
        }
        """
        if self.mcp_server_url:
            return self._call_http_mcp(method, params)
        elif self.mcp_server_path:
            return self._call_local_mcp(method, params)
        else:
            return None
    
    def _call_http_mcp(self, method: str, params: Dict = None) -> Optional[Dict]:
        """Call MCP server via HTTP"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": int(datetime.now().timestamp() * 1000),
                "method": method,
                "params": params or {}
            }
            
            response = requests.post(
                self.mcp_server_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                # Check for error, but ignore if error is None (some servers include "error": null)
                if "error" in result and result.get("error") is not None:
                    error_msg = result.get("error", {})
                    if isinstance(error_msg, dict):
                        error_msg = error_msg.get("message", str(error_msg))
                    print(f"MCP Error: {error_msg}")
                    return None
                return result.get("result")
            
            # Try GET request for health check or different endpoints
            if response.status_code == 404:
                # Try common MCP endpoints
                endpoints_to_try = [
                    f"{self.mcp_server_url}/mcp",
                    f"{self.mcp_server_url}/api/mcp",
                    f"{self.mcp_server_url}/v1/mcp"
                ]
                for endpoint in endpoints_to_try:
                    try:
                        test_response = requests.get(endpoint, timeout=5)
                        if test_response.status_code == 200:
                            print(f"Found MCP endpoint at: {endpoint}")
                            # Retry POST to this endpoint
                            response = requests.post(
                                endpoint,
                                json=payload,
                                headers={"Content-Type": "application/json"},
                                timeout=10
                            )
                            if response.status_code == 200:
                                result = response.json()
                                if "error" not in result:
                                    return result.get("result")
                    except:
                        continue
            
            # Only print error if it's not a 500 (server error - might be temporary)
            if response.status_code != 500:
                print(f"MCP HTTP Error: Status {response.status_code} from {self.mcp_server_url}")
            else:
                # For 500 errors, try to get more details
                try:
                    error_detail = response.json()
                    print(f"MCP Server Error (500): {error_detail.get('error', {}).get('message', 'Internal server error')}")
                except:
                    print(f"MCP Server Error (500): Internal server error - check server logs")
            return None
            
        except requests.exceptions.ConnectionError as e:
            print(f"MCP Connection Error: Could not connect to {self.mcp_server_url}")
            print(f"  Error: {str(e)}")
            print(f"  Please verify:")
            print(f"  1. The MCP server is running on {self.mcp_server_url}")
            print(f"  2. The port is correct (default is 3000)")
            print(f"  3. Firewall allows connections")
            return None
        except requests.exceptions.Timeout:
            print(f"MCP Timeout: Server at {self.mcp_server_url} did not respond in time")
            return None
        except Exception as e:
            print(f"MCP Error: {str(e)}")
            return None
    
    def _call_local_mcp(self, method: str, params: Dict = None) -> Optional[Dict]:
        """Call MCP server via local command/process"""
        try:
            # Build command
            cmd = [self.mcp_server_path]
            if method:
                cmd.extend(["--method", method])
            if params:
                cmd.extend(["--params", json.dumps(params)])
            
            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout) if result.stdout else {}
            
            return None
            
        except Exception as e:
            return None
    
    def list_tools(self, force_refresh: bool = False) -> List[Dict]:
        """
        List available tools from MCP server
        
        Returns:
            List of tool definitions with name, description, parameters
        """
        if not force_refresh and self.tools_cache:
            return list(self.tools_cache.values())
        
        result = self._call_mcp_server("tools/list")
        
        if result and "tools" in result:
            tools = result["tools"]
            self.tools_cache = {tool["name"]: tool for tool in tools}
            return tools
        
        return []
    
    def get_tool(self, tool_name: str) -> Optional[Dict]:
        """Get specific tool definition"""
        if tool_name in self.tools_cache:
            return self.tools_cache[tool_name]
        
        # Refresh cache
        self.list_tools(force_refresh=True)
        return self.tools_cache.get(tool_name)
    
    def call_tool(self, tool_name: str, arguments: Dict = None) -> Optional[Dict]:
        """
        Call a tool on the MCP server
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
        
        Returns:
            Tool execution result
        """
        result = self._call_mcp_server("tools/call", {
            "name": tool_name,
            "arguments": arguments or {}
        })
        
        return result
    
    def list_resources(self, force_refresh: bool = False) -> List[Dict]:
        """
        List available resources from MCP server
        
        Returns:
            List of resource definitions
        """
        if not force_refresh and self.resources_cache:
            return list(self.resources_cache.values())
        
        result = self._call_mcp_server("resources/list")
        
        if result and "resources" in result:
            resources = result["resources"]
            self.resources_cache = {res["uri"]: res for res in resources}
            return resources
        
        return []
    
    def get_resource(self, uri: str) -> Optional[Dict]:
        """
        Get a resource from MCP server
        
        Args:
            uri: Resource URI
        
        Returns:
            Resource content and metadata
        """
        result = self._call_mcp_server("resources/read", {
            "uri": uri
        })
        
        return result
    
    def list_prompts(self) -> List[Dict]:
        """List available prompts from MCP server"""
        result = self._call_mcp_server("prompts/list")
        
        if result and "prompts" in result:
            return result["prompts"]
        
        return []
    
    def get_prompt(self, prompt_name: str, arguments: Dict = None) -> Optional[str]:
        """
        Get a prompt template from MCP server
        
        Args:
            prompt_name: Name of the prompt
            arguments: Variables to fill in the prompt template
        
        Returns:
            Rendered prompt text
        """
        result = self._call_mcp_server("prompts/get", {
            "name": prompt_name,
            "arguments": arguments or {}
        })
        
        if result and "messages" in result:
            # MCP prompts return messages array
            return "\n".join([msg.get("content", "") for msg in result["messages"]])
        
        return None
    
    def get_server_info(self) -> Optional[Dict]:
        """Get MCP server information"""
        result = self._call_mcp_server("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "mo11y-agent",
                "version": "1.0.0"
            }
        })
        
        return result
    
    def search_resources(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search resources by query
        
        Args:
            query: Search query
            limit: Maximum results
        
        Returns:
            List of matching resources
        """
        resources = self.list_resources()
        
        # Simple text search (can be enhanced)
        query_lower = query.lower()
        matches = []
        
        for resource in resources:
            name = resource.get("name", "").lower()
            description = resource.get("description", "").lower()
            uri = resource.get("uri", "").lower()
            
            if query_lower in name or query_lower in description or query_lower in uri:
                matches.append(resource)
                if len(matches) >= limit:
                    break
        
        return matches
