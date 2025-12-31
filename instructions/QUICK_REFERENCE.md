# Quick Reference Guide

Quick access to common tasks and information.

## Most Common Tasks

### Starting the App
```bash
# With spaCy (recommended)
source venv/bin/activate
streamlit run app_enhanced.py

# Without spaCy
streamlit run app_enhanced.py
```

### Switching Models
Edit `config.json`:
```json
{
  "model_name": "your-model-name:latest"
}
```
See: `instructions/features/MODEL_SWITCHING_GUIDE.md`

### Switching Personas
Use the persona dropdown in the Streamlit sidebar.
See: `instructions/features/PERSONA_SWITCHER_GUIDE.md`

### Starting MCP Server
```bash
python3 local_mcp_server.py
```
See: `instructions/setup/QUICK_START_MCP.md`

## Key Features

### Separate Chat Histories
Each persona maintains its own conversation thread.
See: `instructions/features/PERSONA_CHAT_HISTORY.md`

### RAG Files
RAG files automatically load related files (family members, etc.).
See: `instructions/features/RAG_LOADING_IMPROVEMENTS.md`

### Tool Builder Persona
Create MCP tools easily with the Tool Builder persona.
See: `instructions/features/TOOL_BUILDER_PERSONA.md`

### spaCy NLP
Enhanced entity extraction for life journal.
See: `instructions/SPACY_GUIDE.md`

## File Locations

- **Personas**: `sonas/*.json`
- **RAG Files**: `RAGs/*.json`
- **Config**: `config.json`
- **Database**: `SPOHNZ.db` or `mo11y_companion.db`
- **MCP Server**: `local_mcp_server.py`

## Documentation

- **Main README**: `README.md`
- **Architecture**: `ARCHITECTURE.md`
- **Complete Guide**: `instructions.md`
- **All Instructions**: `instructions/` directory
- **Task Log**: `instructions/TASK_LOG.md`

## Troubleshooting

1. **Model not found**: Check `ollama list` and update `config.json`
2. **MCP not working**: Start MCP server (`python3 local_mcp_server.py`)
3. **spaCy not working**: Activate venv (`source venv/bin/activate`)
4. **Persona not loading**: Check `sonas/` directory for JSON files

## Quick Links

- Setup Guides: `instructions/setup/`
- Feature Guides: `instructions/features/`
- Technical Docs: `instructions/technical/`
- Reference: `instructions/reference/`
