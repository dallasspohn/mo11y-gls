# Setup Assessment: Backend Server + Voice Integration

## Overview

This document assesses the time and effort required to:
1. Set up Ubuntu server (192.168.1.225) as backend
2. Add voice interface using Samsung S9 phone

---

## Part 1: Backend Server Setup (192.168.1.225)

### Time Estimate: **2-4 hours** (first time) | **30 minutes** (if you're familiar)

### What's Already Built:
✅ `server_agent.py` - ServerMo11yAgent class exists  
✅ `SERVER_SETUP.md` - Documentation exists  
✅ Remote Ollama connection support  

### What Needs to Be Done:

#### Step 1: Server Setup (1-2 hours)
- [ ] SSH into Ubuntu server
- [ ] Install Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
- [ ] Pull your model: `ollama pull Izzy-Chan` (or your model)
- [ ] Configure firewall: `sudo ufw allow 11434/tcp`
- [ ] Test: `curl http://localhost:11434/api/tags`
- [ ] Set up Ollama as service (optional but recommended)

#### Step 2: Update Client Code (30 minutes)
- [ ] Modify `app_enhanced.py` to use `ServerMo11yAgent`
- [ ] Update `config.json` with server IP
- [ ] Test connection

#### Step 3: Optional API Gateway (1-2 hours)
- [ ] Create FastAPI wrapper (see SERVER_SETUP.md)
- [ ] Add authentication/security
- [ ] Better error handling

### Code Changes Needed:

**Option A: Simple (30 min)**
```python
# In app_enhanced.py, replace:
from mo11y_agent import create_mo11y_agent

# With:
from server_agent import create_server_agent

agent = create_server_agent(
    model_name=CONFIG["model_name"],
    db_path=CONFIG["db_path"],
    sona_path=sona_path,
    ollama_host="http://192.168.1.225",
    ollama_port=11434
)
```

**Option B: Full API Backend (2-3 hours)**
- Create FastAPI server on Ubuntu
- Move all agent logic to backend
- Streamlit becomes pure UI client

---

## Part 2: Voice Integration (Samsung S9)

### Time Estimate: **8-16 hours** (first time) | **4-6 hours** (if experienced)

### Architecture Overview:

```
Samsung S9 Phone (Voice Client)
    ↓ (HTTP/WebSocket)
Ubuntu Server (192.168.1.225)
    ├── FastAPI Backend API
    ├── Mo11y Agent
    ├── Ollama LLM
    └── Audio Processing Service
    ↓ (HTTP/WebSocket)
Samsung S9 Phone (Audio Response)
```

### Components Needed:

#### 1. **Voice Input (Speech-to-Text)** - 2-3 hours
   - **Option A: Google Speech-to-Text API** (easiest, ~$0.006 per minute)
   - **Option B: Whisper (OpenAI)** - Free, runs on server
   - **Option C: Android SpeechRecognizer** - Built-in, free
   
   **Recommendation:** Start with Android SpeechRecognizer (free, works offline)

#### 2. **Voice Output (Text-to-Speech)** - 1-2 hours
   - **Option A: Google TTS API** (paid)
   - **Option B: pyttsx3** - Free, runs on server
   - **Option C: Android TextToSpeech** - Built-in, free
   
   **Recommendation:** Android TextToSpeech (free, good quality)

#### 3. **Mobile App** - 4-8 hours
   - **Option A: Simple Android App** (Kotlin/Java)
   - **Option B: React Native** (cross-platform)
   - **Option C: Flutter** (cross-platform)
   - **Option D: Web App** (PWA, works on phone browser)
   
   **Recommendation:** Start with Web App (PWA) - fastest, no app store needed

#### 4. **Backend API Endpoints** - 2-3 hours
   - `/api/chat` - Text chat (already exists concept)
   - `/api/chat/voice` - Voice chat endpoint
   - `/api/audio/upload` - Upload audio file
   - `/api/audio/stream` - Stream audio response

#### 5. **Real-time Communication** - 2-3 hours
   - WebSocket for streaming responses
   - Audio streaming
   - Connection management

### Implementation Options:

#### **Option 1: Web App (PWA) - FASTEST** ⭐ Recommended
**Time: 4-6 hours**

- Create HTML/JS web app
- Use Web Speech API (browser-based)
- Works on Samsung S9 browser
- No app installation needed
- Can be added to home screen

**Pros:**
- Fastest to implement
- No app store approval
- Easy updates
- Works on any device

**Cons:**
- Requires internet connection
- Browser limitations

#### **Option 2: Native Android App**
**Time: 8-12 hours**

- Build Android app (Kotlin/Java)
- Use Android SpeechRecognizer
- Use Android TextToSpeech
- Connect to backend API

**Pros:**
- Better performance
- Offline capabilities
- Native UI

**Cons:**
- More development time
- App store deployment
- Platform-specific

#### **Option 3: Hybrid (React Native/Flutter)**
**Time: 10-16 hours**

- Cross-platform framework
- Can deploy to iOS later
- Native modules for voice

**Pros:**
- Cross-platform
- Good performance

**Cons:**
- More complex setup
- Longer development time

---

## Recommended Implementation Plan

### Phase 1: Backend Server (Day 1 - 2-4 hours)
1. ✅ Set up Ollama on Ubuntu server
2. ✅ Update client to use ServerMo11yAgent
3. ✅ Test connection
4. ✅ Optional: Create FastAPI wrapper

### Phase 2: Voice Web App (Day 2-3 - 6-8 hours)
1. ✅ Create simple HTML/JS web app
2. ✅ Add Web Speech API for STT
3. ✅ Add Web Speech API for TTS
4. ✅ Connect to backend API
5. ✅ Add WebSocket for streaming
6. ✅ Test on Samsung S9 browser

### Phase 3: Polish & Deploy (Day 4 - 2-4 hours)
1. ✅ Add error handling
2. ✅ Add loading states
3. ✅ Optimize audio quality
4. ✅ Add PWA manifest (installable)
5. ✅ Deploy to server

**Total Time: 10-16 hours** (spread over 3-4 days)

---

## Technical Stack Recommendations

### Backend (Ubuntu Server):
- **FastAPI** - Modern Python web framework
- **WebSocket** - Real-time communication
- **Whisper** (optional) - Server-side STT
- **pyttsx3** or **gTTS** - Server-side TTS

### Frontend (Samsung S9):
- **Web Speech API** - Browser-based STT/TTS
- **WebSocket** - Real-time communication
- **PWA** - Installable web app

### Database:
- **SQLite** (current) - Fine for single user
- **PostgreSQL** (optional) - If scaling needed

---

## Cost Estimate

### Backend Server:
- **Free** - Using existing Ubuntu server
- **Optional:** Domain name ($10-15/year)

### Voice APIs:
- **Free** - Using browser Web Speech API
- **Optional:** Google Cloud Speech-to-Text ($0.006/min)
- **Optional:** Google Cloud Text-to-Speech ($4 per 1M characters)

### Total: **$0-20/year** (depending on usage)

---

## Quick Start Commands

### On Ubuntu Server (192.168.1.225):
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull Izzy-Chan

# Allow firewall
sudo ufw allow 11434/tcp

# Test
curl http://localhost:11434/api/tags
```

### On Client Machine:
```python
# Update app_enhanced.py
from server_agent import create_server_agent

agent = create_server_agent(
    model_name="Izzy-Chan",
    ollama_host="http://192.168.1.225",
    ollama_port=11434
)
```

---

## Next Steps

1. **Decide on approach:**
   - Web App (fastest) ✅ Recommended
   - Native Android App (better UX)
   - Hybrid (cross-platform)

2. **Set up backend first** (2-4 hours)
   - Get server working
   - Test connection

3. **Build voice interface** (6-8 hours)
   - Start with web app
   - Add voice features
   - Test on Samsung S9

4. **Iterate and improve** (ongoing)
   - Add features
   - Improve UX
   - Optimize performance

---

## Questions to Consider

1. **Do you want offline voice support?**
   - Yes → Native Android app
   - No → Web app is fine

2. **Do you need iOS support later?**
   - Yes → Consider React Native/Flutter
   - No → Android/Web is fine

3. **What's your priority?**
   - Speed → Web app (4-6 hours)
   - Quality → Native app (8-12 hours)
   - Cross-platform → Hybrid (10-16 hours)

---

## Summary

| Task | Time Estimate | Difficulty |
|------|--------------|------------|
| Backend Server Setup | 2-4 hours | Easy |
| Voice Web App | 4-6 hours | Medium |
| Voice Native App | 8-12 hours | Hard |
| Full Integration | 10-16 hours | Medium-Hard |

**Recommended Path:**
1. Backend server (2-4 hours) ✅
2. Voice web app (4-6 hours) ✅
3. Total: **6-10 hours** for basic setup

**Can be done in a weekend!** 🎉
