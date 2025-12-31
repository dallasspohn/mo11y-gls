"""
MCP Tool: Image Generator using FREE Stable Diffusion
Generates images from text prompts using Hugging Face Inference API (free tier)
"""

from typing import Dict, Any, Optional
import os


def generate_image_tool(arguments: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate an image from a text prompt using FREE Stable Diffusion (no payment required)
    
    Args:
        arguments: Dictionary containing:
            - prompt (str, required): Text description of the image to generate
            - style (str, optional): Style preset (not used by Stable Diffusion but kept for compatibility)
            - negative_prompt (str, optional): What to avoid in the image
            - width (int, optional): Image width in pixels (default: 1024)
            - height (int, optional): Image height in pixels (default: 1024)
        context: Optional context dictionary
    
    Returns:
        Dictionary with:
            - success (bool): Whether generation succeeded
            - image_path (str): Path to generated image file
            - error (str): Error message if failed
    """
    try:
        prompt = arguments.get("prompt")
        if not prompt:
            return {
                "success": False,
                "error": "Prompt is required"
            }
        
        # Import here to avoid circular dependencies
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from external_apis import ExternalAPIManager
        
        # Initialize API manager (use default DB path)
        api_manager = ExternalAPIManager()
        
        # Check if Hugging Face API is registered, if not, register it
        if "huggingface_image" not in api_manager.api_configs:
            api_manager.register_huggingface_image_api()
        
        # Generate image
        style = arguments.get("style", "default")
        negative_prompt = arguments.get("negative_prompt")
        width = arguments.get("width", 1024)
        height = arguments.get("height", 1024)
        
        image_path = api_manager.generate_image(
            prompt=prompt,
            style=style,
            negative_prompt=negative_prompt,
            width=width,
            height=height
        )
        
        if image_path and os.path.exists(image_path):
            return {
                "success": True,
                "image_path": image_path,
                "prompt": prompt
            }
        else:
            return {
                "success": False,
                "error": "Image generation failed or file not found"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error generating image: {str(e)}"
        }


# Tool metadata for MCP server
TOOL_METADATA = {
    "name": "generate_image",
    "description": "Generate an image from a text prompt using FREE Stable Diffusion AI model (no payment required). Creates images based on your description.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Text description of the image you want to generate (e.g., 'a sunset over mountains', 'a futuristic cityscape')"
            },
            "style": {
                "type": "string",
                "description": "Style preset (optional, not currently used by FLUX but kept for compatibility)",
                "default": "default"
            },
            "negative_prompt": {
                "type": "string",
                "description": "What to avoid in the image (optional, e.g., 'blurry, low quality')"
            },
            "width": {
                "type": "integer",
                "description": "Image width in pixels (default: 1024)",
                "default": 1024
            },
            "height": {
                "type": "integer",
                "description": "Image height in pixels (default: 1024)",
                "default": 1024
            }
        },
        "required": ["prompt"]
    }
}
