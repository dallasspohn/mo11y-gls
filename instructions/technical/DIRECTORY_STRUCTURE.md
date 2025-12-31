# Mo11y Directory Structure

## Active Files (Root Directory)

### Core Application
- `app_enhanced.py` - **Main Streamlit UI** (run with `streamlit run app_enhanced.py`)
- `mo11y_agent.py` - LangGraph agent implementation
- `config.json` - Configuration file (model, paths, etc.)

### Core Components
- `enhanced_memory.py` - Multi-modal memory system (images, audio, episodic, semantic)
- `companion_engine.py` - Personality evolution engine
- `life_journal.py` - Life journal system (for Alex Mercer persona)
- `relationship_timeline.py` - Visualization tools

### Integration Modules
- `external_apis.py` - External API integration (calendar, weather, notes)
- `mcp_integration.py` - MCP server integration (docker-mcp)
- `server_agent.py` - Server-based agent for remote Ollama

### Documentation
- `README.md` - Main documentation
- `README_ENHANCED.md` - Enhanced features documentation
- `ARCHITECTURE.md` - Technical architecture
- `ALEX_MERCER_SETUP.md` - Alex Mercer persona setup
- `SERVER_SETUP.md` - Server deployment guide
- `SETUP_ASSESSMENT.md` - Backend/voice setup assessment
- `MULTIMODAL_MCP_SETUP.md` - Multi-modal & MCP integration guide
- `FAST_MODELS.md` - Fast model recommendations

### Configuration & Dependencies
- `requirements.txt` - Python dependencies
- `life-journal.json` - Life journal data (for Alex Mercer)

### Data Directories
- `sonas/` - Persona files (JSON)
- `RAGs/` - RAG knowledge bases
- `text/` - Text files for RAG
- `pdf/` - PDF documents
- `MASTER_PLAN/` - Master plan documents
- `media/` - Media storage (images, audio) - created automatically
- `SPOHNZ.db` - SQLite database

### Archive
- `archive/` - Old/unused files (see archive/README.md)

## Archived Files

All old files have been moved to `archive/` directory:

### Old Applications
- `app.py` - Original Streamlit app
- `molly-lite.py` - Lite version
- `ai-assistant.py` - Old assistant
- `july.py` - Old script

### Old Components
- `memory.py` - Simple memory (replaced by enhanced_memory.py)
- `Color.py` - Old utility

### Old Scripts
- `rag_file_upload.py` - Old RAG upload
- `vecotor.py` - Typo file
- `streamlit_run_ai-assistant` - Old run script
- `switch_model.py` - Model switching script
- `switch_model.sh` - Shell script

### Old Documentation
- `molly-lite-README.md` - Old README

### Old Data
- `reviews.csv` - Old reviews

### Old Apps Directory
- `archive/old-apps/` - Multiple old app versions

## Quick Start

1. **Run the application:**
   ```bash
   streamlit run app_enhanced.py
   ```

2. **Configure model in `config.json`:**
   ```json
   {
       "model_name": "llama3.2:3b"
   }
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## File Organization

```
mo11y/
├── app_enhanced.py          # Main UI
├── mo11y_agent.py           # Agent core
├── enhanced_memory.py       # Memory system
├── companion_engine.py      # Personality
├── external_apis.py         # API integration
├── mcp_integration.py       # MCP integration
├── server_agent.py          # Server agent
├── config.json              # Configuration
├── requirements.txt         # Dependencies
├── README.md                # Main docs
├── sonas/                   # Personas
├── RAGs/                    # Knowledge bases
├── text/                    # Text files
├── media/                   # Media storage
├── archive/                 # Old files
└── SPOHNZ.db               # Database
```

## Notes

- All active code is in the root directory
- Old/unused files are in `archive/`
- Database and media files are created automatically
- Configuration is in `config.json`
