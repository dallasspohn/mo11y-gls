"""
MCP Tools Module
Custom tools for the local MCP server

To add a new tool:
1. Create tool_name.py in this directory
2. Add: from .tool_name import tool_handler
3. Add tool_handler to __all__
4. Register in local_mcp_server.py
"""

# Import all tools here for easy registration
__all__ = []

try:
    from .file_reader import file_reader_tool
    __all__.append('file_reader_tool')
except ImportError:
    pass

try:
    from .textcase import textcase_handler
    __all__.append('textcase_handler')
except ImportError:
    pass

try:
    from .image_generator import generate_image_tool, TOOL_METADATA as IMAGE_GENERATOR_METADATA
    __all__.append('generate_image_tool')
    __all__.append('IMAGE_GENERATOR_METADATA')
except ImportError:
    pass
