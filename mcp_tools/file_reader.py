"""
File Reader Tool
Reads a text file and returns its contents
"""

from typing import Dict


def file_reader_tool(arguments: Dict) -> Dict:
    """
    Reads a text file and returns its contents in JSON-RPC format.
    
    Args:
        arguments: Dictionary containing:
            - filename (str): Path to the text file to be read
    
    Returns:
        Dictionary with "content" key containing text content,
        and "isError" indicating if there was an error reading the file.
    """
    try:
        # Extract filename parameter
        filename = arguments.get("filename")
        
        if not filename:
            return {
                "content": [{"type": "text", "text": "Error: filename parameter is required"}],
                "isError": True
            }
        
        # Validate that the file exists and read it
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "content": [{"type": "text", "text": content}],
            "isError": False
        }
    
    except FileNotFoundError:
        # Handle case where file doesn't exist
        return {
            "content": [{"type": "text", "text": f"File not found: {filename}"}],
            "isError": True
        }
    
    except PermissionError:
        return {
            "content": [{"type": "text", "text": f"Permission denied: {filename}"}],
            "isError": True
        }
    
    except Exception as e:
        # Handle any other errors reading the file
        error_msg = str(e)
        return {
            "content": [{"type": "text", "text": f"Failed to read file: {error_msg}"}],
            "isError": True
        }
