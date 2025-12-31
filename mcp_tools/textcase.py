"""
Text Case Converter
Converts text to uppercase or lowercase based on parameters.
"""

from typing import Dict


def textcase_handler(arguments: Dict) -> Dict:
    """
    Text Case Converter Tool Handler
    
    Args:
        arguments: Dictionary containing:
            - text (str): The input text to be converted
            - mode (str, optional): Conversion mode. Accepts "uppercase" or "lowercase"
    
    Returns:
        Dictionary with "content" array and "isError" flag
    """
    try:
        # Extract parameters
        text = arguments.get("text")
        
        if not text:
            return {
                "content": [{"type": "text", "text": "Error: text parameter is required"}],
                "isError": True
            }
        
        mode = arguments.get("mode", "lowercase")
        mode_lower = mode.lower() if mode else "lowercase"
        
        # Convert based on mode
        if mode_lower == "uppercase":
            result = text.upper()
        elif mode_lower == "lowercase":
            result = text.lower()
        else:
            return {
                "content": [{"type": "text", "text": f"Error: mode must be 'uppercase' or 'lowercase', got '{mode}'"}],
                "isError": True
            }
        
        return {
            "content": [{"type": "text", "text": result}],
            "isError": False
        }
    
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }
