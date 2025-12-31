# Server Setup Guide

## Why Move to Server?

The connection refused error happens because:
1. Ollama server must be running locally
2. Connection can fail if server crashes
3. No retry logic or connection pooling
4. Hard to scale or monitor

## Server Architecture Options

### Option 1: Remote Ollama (Simplest)

Keep current code, just point to remote server:

```python
# In app_enhanced.py, use ServerMo11yAgent
from server_agent import create_server_agent

agent = create_server_agent(
    model_name="Izzy-Chan",
    ollama_host="http://your-server-ip",
    ollama_port=11434
)
```

**Requirements:**
- Ollama running on remote server
- Network access to server
- Firewall allows port 11434

### Option 2: API Gateway (Recommended)

Create FastAPI backend that wraps Ollama:

**Backend (api_server.py):**
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ollama import chat
import os

app = FastAPI()

# CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    model: str = "Izzy-Chan"
    system_prompt: str = None
    context: dict = None

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.message})
        
        stream = chat(
            model=request.model,
            messages=messages,
            stream=True,
        )
        
        response = ""
        for chunk in stream:
            response += chunk["message"]["content"]
        
        return {"response": response, "error": None}
    except Exception as e:
        return {"response": None, "error": str(e)}

@app.get("/api/health")
async def health_check():
    try:
        from ollama import list
        models = list()
        return {"status": "healthy", "models": [m["name"] for m in models.get("models", [])]}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

**Run backend:**
```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

**Update Streamlit app:**
```python
import requests

def chat_via_api(message: str, system_prompt: str = None):
    response = requests.post(
        "http://your-server:8000/api/chat",
        json={
            "message": message,
            "model": "Izzy-Chan",
            "system_prompt": system_prompt
        }
    )
    return response.json()
```

### Option 3: Full Backend Service

Complete backend with:
- Memory management
- Life journal
- Personality engine
- All agent logic

**Benefits:**
- Streamlit is just UI
- Backend handles all logic
- Can support multiple clients
- Better error handling
- Easier to scale

## Quick Server Setup

### On Server Machine:

1. **Install Ollama:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

2. **Pull model:**
```bash
ollama pull Izzy-Chan
```

3. **Configure firewall:**
```bash
# Allow port 11434
sudo firewall-cmd --add-port=11434/tcp --permanent
sudo firewall-cmd --reload
```

4. **Test:**
```bash
curl http://localhost:11434/api/tags
```

### On Client Machine:

1. **Set environment variable:**
```bash
export OLLAMA_HOST=http://your-server-ip:11434
```

2. **Or update code:**
```python
import os
os.environ['OLLAMA_HOST'] = 'http://your-server-ip:11434'
```

3. **Use ServerMo11yAgent:**
```python
from server_agent import create_server_agent

agent = create_server_agent(
    model_name="Izzy-Chan",
    ollama_host="http://your-server-ip",
    ollama_port=11434
)
```

## Docker Option

### Docker Compose Setup:

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

volumes:
  ollama_data:
```

Run: `docker-compose up -d`

## Monitoring

Add health checks:

```python
def check_server_health():
    try:
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False
```

## Security Considerations

1. **Authentication** - Add API keys or OAuth
2. **Rate Limiting** - Prevent abuse
3. **HTTPS** - Encrypt connections
4. **Firewall** - Restrict access
5. **Monitoring** - Log requests, track usage

## Recommended Path

1. **Start Simple**: Use ServerMo11yAgent with remote Ollama
2. **Add API Layer**: Create FastAPI wrapper for better control
3. **Full Backend**: Move all logic to backend service

---

**The connection error happens because Ollama isn't running or accessible. Moving to a server gives you reliability and scalability.**
