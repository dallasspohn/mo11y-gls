#!/usr/bin/env python3
"""
Quick check if MCP server is running and accessible
"""

import requests
import sys
import json
import os

def get_mcp_server_url():
    """Get MCP server URL from environment variable or config.json"""
    # Check environment variable first
    mcp_url = os.getenv("MCP_SERVER_URL")
    if mcp_url:
        return mcp_url
    
    # Try to read from config.json
    try:
        config_path = "config.json"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                mcp_url = config.get("mcp_server_url") or config.get("MCP_SERVER_URL")
                if mcp_url:
                    return mcp_url
    except Exception:
        pass
    
    # Default fallback
    return "http://localhost:8443"

def check_server(url=None):
    """Check if MCP server is running"""
    print(f"Checking MCP server at: {url}")
    print("="*60)
    
    # Try health endpoint
    try:
        response = requests.get(f"{url}/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print("✅ Server is running!")
            print(f"   Status: {data.get('status')}")
            print(f"   Tools: {data.get('tools')}")
            print(f"   Resources: {data.get('resources')}")
            print(f"   Prompts: {data.get('prompts')}")
            return True
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection refused - server is NOT running on {url}")
        print("\n💡 To start the server:")
        print("   python3 local_mcp_server.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Try tools/list endpoint
    try:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        response = requests.post(f"{url}/", json=request, timeout=2)
        if response.status_code == 200:
            result = response.json()
            if "result" in result and "tools" in result["result"]:
                tools = result["result"]["tools"]
                print(f"\n✅ Tools endpoint works! Found {len(tools)} tools:")
                for tool in tools:
                    print(f"   - {tool['name']}")
                return True
    except Exception as e:
        print(f"⚠️  Tools endpoint error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = get_mcp_server_url()
        print(f"Using MCP server URL from config: {url}")
    
    success = check_server(url)
    sys.exit(0 if success else 1)
