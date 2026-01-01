# Multi-Modal Memory & MCP Integration Setup Guide

## Overview

This guide covers the new features added to Mo11y:
1. **Multi-Modal Memory** - Store and recall images and audio
2. **External API Integration** - Connect to calendar, weather, notes, etc.
3. **MCP Server Integration** - Connect to docker-mcp server

---

## 1. Multi-Modal Memory

### Features

- **Image Storage**: Store images with descriptions and thumbnails
- **Audio Storage**: Store audio files with transcriptions
- **Video Storage**: Support for video files (future)
- **Automatic Thumbnails**: Images get thumbnails generated automatically
- **File Deduplication**: Uses SHA256 hashing to avoid duplicates

### Database Schema

New table: `media_memories`
- Links media files to episodic memories
- Stores file paths, hashes, metadata
- Supports descriptions and transcriptions

### Usage

```python
from enhanced_memory import EnhancedMemory

memory = EnhancedMemory("mo11y_companion.db")

# Store an image
memory_id = memory.remember_episodic(
    content="User shared a photo of their cat",
    importance=0.8
)

media_id = memory.remember_media(
    memory_id=memory_id,
    media_type="image",
    file_path="/path/to/image.jpg",
    description="A cute orange tabby cat",
    metadata={"width": 1920, "height": 1080}
)

# Recall media
media_items = memory.recall_media(memory_id=memory_id, media_type="image")
```

### Media Storage Structure

```
mo11y/
├── mo11y_companion.db
└── media/
    ├── images/
    │   └── {memory_id}_{hash}.jpg
    ├── audio/
    │   └── {memory_id}_{hash}.mp3
    └── thumbnails/
        └── thumb_{filename}.jpg
```

---

## 2. External API Integration

### Supported APIs

- **Calendar**: Google Calendar, CalDAV
- **Notes**: Obsidian, Joplin
- **Weather**: OpenWeatherMap, WeatherAPI.com
- **Generic**: Any REST API

### Setup

#### Register an API

```python
from external_apis import ExternalAPIManager

api_manager = ExternalAPIManager("mo11y_companion.db")

# Register Google Calendar
api_manager.register_api(
    api_name="calendar",
    api_type="google_calendar",
    config={
        "api_key": "your-api-key",
        "calendar_id": "primary"
    }
)

# Register Obsidian Notes
api_manager.register_api(
    api_name="notes",
    api_type="obsidian",
    config={
        "vault_path": "/path/to/obsidian/vault"
    }
)

# Register Weather API
api_manager.register_api(
    api_name="weather",
    api_type="openweathermap",
    config={
        "api_key": "your-api-key",
        "default_location": "Crandall, TX"
    }
)
```

#### Use APIs

```python
# Get calendar events
events = api_manager.get_calendar_events(days_ahead=7)

# Get weather
weather = api_manager.get_weather(location="Crandall, TX")

# Get notes
notes = api_manager.get_notes(limit=10)

# Generic API call
result = api_manager.call_api(
    api_name="custom_api",
    endpoint="users/me",
    method="GET",
    cache_ttl=300
)
```

### API Configuration Storage

APIs are stored in the database:
- `api_configurations` - API settings
- `api_cache` - Response caching
- `api_call_history` - Monitoring/logging

### Adding New API Types

To add support for a new API:

1. Add method to `ExternalAPIManager`:
```python
def _get_new_api(self, config: Dict) -> List[Dict]:
    # Implementation
    pass
```

2. Register in `get_*` method:
```python
if api_type == "new_api":
    result = self._get_new_api(config)
```

---

## 3. MCP Server Integration

### What is MCP?

Model Context Protocol (MCP) is a protocol for connecting AI assistants to external tools and data sources. The docker-mcp server provides tools and resources that Mo11y can use.

### Setup Docker-MCP Server

#### Option 1: Use Existing Docker Container

```bash
# Check if docker-mcp is running
docker ps | grep docker-mcp

# Start if not running
docker start docker-mcp

# Or run new container
docker run -d --name docker-mcp -p 3000:3000 docker-mcp:latest
```

#### Option 2: Configure via Environment Variables

```bash
export MCP_SERVER_URL="http://localhost:3000"
# OR
export MCP_SERVER_PATH="/path/to/mcp-server"
```

### Usage in Agent

The agent automatically connects to MCP if available:

```python
from mo11y_agent import create_mo11y_agent

agent = create_mo11y_agent(
    model_name="Izzy-Chan",
    enable_mcp=True  # Default: True
)

# MCP tools are automatically available in context
# Agent can use tools when generating responses
```

### Manual MCP Tool Execution

```python
from mcp_integration import MCPClient, MCPToolExecutor

# Create client
mcp_client = MCPClient(mcp_server_url="http://localhost:3000")

# List available tools
tools = mcp_client.list_tools()
for tool in tools:
    print(f"{tool['name']}: {tool['description']}")

# Execute a tool
result = mcp_client.call_tool(
    tool_name="docker_list_containers",
    arguments={"all": True}
)

# Use executor
executor = MCPToolExecutor(mcp_client)
result = executor.execute_tool(
    tool_name="docker_list_containers",
    arguments={"all": True},
    context={"user": "dallas"}
)
```

### MCP Resources

```python
# List resources
resources = mcp_client.list_resources()

# Get a resource
resource = mcp_client.get_resource("docker://container/name")

# Search resources
matches = mcp_client.search_resources("docker", limit=10)
```

### Docker-MCP Helper

```python
from mcp_integration import DockerMCPServer

# Check if running
if DockerMCPServer.check_docker_mcp_running():
    print("MCP server is running")

# Start server
DockerMCPServer.start_docker_mcp()

# Get URL
url = DockerMCPServer.get_docker_mcp_url()
```

---

## 4. Integration with Agent

### Automatic Integration

The agent automatically:
- Loads external API context (calendar, weather, notes)
- Includes MCP tools in context
- Stores media files when attached
- Uses MCP tools when appropriate

### Agent State Updates

The agent now supports media in state:

```python
result = agent.chat(
    user_input="Check my calendar",
    config={
        "has_media": True,
        "media_files": [
            {
                "type": "image",
                "path": "/path/to/image.jpg",
                "description": "Photo from user"
            }
        ]
    }
)
```

### Context Flow

```
User Input
    ↓
Analyze Input (detect media, API needs, tool needs)
    ↓
Retrieve Memories (including media)
    ↓
Get External Context (calendar, weather, notes)
    ↓
Get MCP Tools Context
    ↓
Generate Response (with all context)
    ↓
Store Memory (including media)
```

---

## 5. UI Updates Needed

### Streamlit App Updates

Update `app_enhanced.py` to support:

1. **File Upload**:
```python
uploaded_file = st.file_uploader("Upload image or audio", type=['jpg', 'png', 'mp3', 'wav'])
if uploaded_file:
    # Save to temp file
    # Pass to agent
```

2. **Media Display**:
```python
# Show media in memories
media_items = memory.recall_media(memory_id=memory_id)
for media in media_items:
    if media['media_type'] == 'image':
        st.image(media['file_path'])
    elif media['media_type'] == 'audio':
        st.audio(media['file_path'])
```

3. **API Status**:
```python
if agent.external_apis:
    api_status = agent.external_apis.get_api_status()
    st.json(api_status)
```

4. **MCP Tools**:
```python
if agent.mcp_executor:
    tools = agent.mcp_client.list_tools()
    st.write("Available MCP Tools:")
    for tool in tools:
        st.write(f"- {tool['name']}")
```

---

## 6. Dependencies

### New Requirements

Add to `requirements.txt`:

```
# Image processing
Pillow>=10.0.0

# Audio processing (optional)
pydub>=0.25.1

# External APIs
requests>=2.31.0

# MCP (if using HTTP)
requests>=2.31.0

# Calendar (optional)
google-api-python-client>=2.100.0
caldav>=1.3.0
```

### Install

```bash
pip install Pillow requests
# Optional:
pip install google-api-python-client caldav pydub
```

---

## 7. Configuration

### Environment Variables

```bash
# MCP Server
export MCP_SERVER_URL="http://localhost:3000"
export MCP_SERVER_PATH="/path/to/mcp-server"

# External APIs (optional)
export GOOGLE_CALENDAR_API_KEY="your-key"
export OPENWEATHER_API_KEY="your-key"
```

### Config File

Add to `config.json`:

```json
{
    "enable_mcp": true,
    "enable_external_apis": true,
    "mcp_server_url": "http://localhost:3000",
    "external_apis": {
        "calendar": {
            "type": "google_calendar",
            "enabled": true
        },
        "weather": {
            "type": "openweathermap",
            "enabled": true
        }
    }
}
```

---

## 8. Testing

### Test Multi-Modal Memory

```python
from enhanced_memory import EnhancedMemory

memory = EnhancedMemory("test.db")

# Create memory
mem_id = memory.remember_episodic("Test memory", importance=0.5)

# Store image
media_id = memory.remember_media(
    mem_id, "image", "/path/to/test.jpg", "Test image"
)

# Recall
media = memory.recall_media(memory_id=mem_id)
assert len(media) > 0
```

### Test External APIs

```python
from external_apis import ExternalAPIManager

api = ExternalAPIManager("test.db")

# Register test API
api.register_api("test", "generic", {"base_url": "https://api.example.com"})

# Test call
result = api.call_api("test", "endpoint", method="GET")
```

### Test MCP Integration

```python
from mcp_integration import MCPClient, DockerMCPServer

# Check docker-mcp
if DockerMCPServer.check_docker_mcp_running():
    client = MCPClient(mcp_server_url=DockerMCPServer.get_docker_mcp_url())
    tools = client.list_tools()
    print(f"Found {len(tools)} tools")
```

---

## 9. Troubleshooting

### Media Not Storing

- Check file permissions
- Verify media directory exists
- Check disk space

### External APIs Not Working

- Verify API keys are correct
- Check network connectivity
- Review API call history in database

### MCP Not Connecting

- Verify docker-mcp container is running
- Check MCP_SERVER_URL environment variable
- Test connection manually:
  ```bash
  curl http://localhost:3000
  ```

---

## 10. Next Steps

1. **Update UI** - Add file upload and media display
2. **Add More APIs** - Integrate more external services
3. **Enhance MCP** - Add more tool integrations
4. **Audio Transcription** - Add Whisper for audio transcription
5. **Image Analysis** - Add vision model for image understanding

---

## Summary

✅ Multi-modal memory for images and audio  
✅ External API integration (calendar, weather, notes)  
✅ MCP server integration (docker-mcp)  
✅ Automatic context inclusion in agent  
✅ Media storage with thumbnails  
✅ API caching and monitoring  

All features are integrated and ready to use!
