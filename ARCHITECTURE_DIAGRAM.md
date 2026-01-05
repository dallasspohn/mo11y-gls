# Mo11y Architecture Diagram

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                          │
├─────────────────────────────────────────────────────────────────┤
│  Streamlit UI (app_enhanced.py)  │  Slack Bot (slack_bot.py) │
│  - Chat Interface                │  - Slack Integration      │
│  - Relationship Stats            │  - Real-time Messaging       │
│  - Memory Vault                  │  - Persona Support           │
│  - Settings                      │  (Telegram optional)         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MO11Y AGENT (mo11y_agent.py)                 │
│                    LangGraph State Machine                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ analyze_input│───▶│retrieve_mem  │───▶│get_personality│     │
│  │              │    │              │    │              │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│         │                    │                    │              │
│         └────────────────────┼────────────────────┘              │
│                              ▼                                    │
│                    ┌──────────────────┐                           │
│                    │generate_response│                           │
│                    └──────────────────┘                           │
│                              │                                    │
│         ┌────────────────────┼────────────────────┐               │
│         ▼                    ▼                    ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │store_memory  │    │adapt_personality│  │check_proactivity│   │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   MEMORY     │   │  PERSONALITY  │   │   SERVICES    │
│   SYSTEM     │   │    ENGINE     │   │               │
│              │   │               │   │               │
│ enhanced_    │   │ companion_    │   │ local_       │
│ memory.py    │   │ engine.py      │   │ calendar.py   │
│              │   │               │   │               │
│ - Episodic   │   │ - Traits:     │   │ reminder_     │
│ - Semantic   │   │   warmth      │   │ service.py    │
│ - Emotional  │   │   playfulness │   │               │
│ - Relations  │   │   empathy     │   │ task_         │
│              │   │   directness  │   │ service.py    │
│              │   │   humor       │   │               │
│              │   │   proactivity │   │               │
│              │   │               │   │               │
└───────────────┘   └───────────────┘   └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                    ┌───────────────────┐
                    │   SQLite Database │
                    │  mo11y_companion.db│
                    │                    │
                    │  - Memories       │
                    │  - Personality    │
                    │  - Preferences    │
                    │  - Calendar       │
                    │  - Tasks          │
                    │  - Reminders      │
                    └───────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  MCP SERVER   │   │  EXTERNAL APIS │   │  LLM (Ollama) │
│               │   │                │   │               │
│ local_mcp_    │   │ external_apis │   │ - deepseek-r1  │
│ server.py      │   │ .py           │   │ - llama3.2:3b │
│               │   │                │   │ - mixtral     │
│ - Tools:       │   │ - Google      │   │               │
│   web_search  │   │   Calendar    │   │               │
│   calculator  │   │ - Weather     │   │               │
│   file_reader  │   │ - Image Gen   │   │               │
│   ollama_chat │   │   (HuggingFace)│   │               │
│   textcase    │   │                │   │               │
│   generate_   │   │                │   │               │
│   image       │   │                │   │               │
└───────────────┘   └───────────────┘   └───────────────┘
```

## Component Interaction Flow

```
User Message
    │
    ▼
┌─────────────────────────────────────┐
│ 1. analyze_input                    │
│    - Extract sentiment              │
│    - Identify topics                │
│    - Detect intent                  │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 2. retrieve_memories                 │
│    - Query episodic memories        │
│    - Get semantic facts             │
│    - Find relevant context          │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 3. get_personality_context          │
│    - Load current traits            │
│    - Get relationship dynamics      │
│    - Apply persona if selected      │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 4. generate_response                │
│    - Build context prompt           │
│    - Call Ollama LLM                │
│    - Filter thinking tokens         │
│    - Format response                │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 5. store_memory                      │
│    - Save as episodic memory        │
│    - Extract semantic facts         │
│    - Record emotional state         │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 6. adapt_personality                │
│    - Adjust traits based on context │
│    - Update relationship dynamics   │
│    - Learn preferences              │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 7. check_proactivity                │
│    - Suggest topics                 │
│    - Recall important memories      │
│    - Celebrate milestones           │
└─────────────────────────────────────┘
    │
    ▼
Response to User
```

## Memory System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY LAYERS                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         EPISODIC MEMORY (Events & Conversations)   │    │
│  │  - Timestamp, Content, Context                     │    │
│  │  - Importance Score, Emotional Valence             │    │
│  │  - Tags, Relationship Context                      │    │
│  └────────────────────────────────────────────────────┘    │
│                        │                                    │
│                        │ Consolidation (30+ days)           │
│                        ▼                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │         SEMANTIC MEMORY (Facts & Knowledge)       │    │
│  │  - Key-Value Pairs                                │    │
│  │  - Confidence Scores                              │    │
│  │  - Access Tracking                                │    │
│  └────────────────────────────────────────────────────┘    │
│                        │                                    │
│                        │                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │         EMOTIONAL MEMORY (Sentiment Patterns)      │    │
│  │  - Emotion Type, Intensity                        │    │
│  │  - Triggers, Context                              │    │
│  │  - Linked to Episodic Memories                    │    │
│  └────────────────────────────────────────────────────┘    │
│                        │                                    │
│                        │                                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │    RELATIONSHIP MEMORY (Milestones & Dynamics)    │    │
│  │  - Significant Moments                             │    │
│  │  - Relationship Growth                             │    │
│  │  - Timeline Tracking                              │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

```
┌──────────────┐
│   User Input │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│              Agent Processing Pipeline                  │
│                                                          │
│  Input → Analysis → Memory Retrieval → Personality      │
│    → LLM Generation → Memory Storage → Personality      │
│    → Proactivity Check → Response                       │
└──────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│              Persistent Storage Layer                    │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │  Memories  │  │ Personality│  │  Services  │       │
│  │  Database  │  │   Traits   │  │  Database  │       │
│  └────────────┘  └────────────┘  └────────────┘       │
└──────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│ User Response│
└──────────────┘
```

## Service Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MO11Y CORE                               │
│              (mo11y_agent.py)                               │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ MCP Client   │ │ Local        │ │ Reminder     │ │ Task         │
│              │ │ Calendar     │ │ Service      │ │ Service      │
│ - Tools      │ │              │ │              │ │              │
│ - Resources  │ │ - Events     │ │ - Alerts     │ │ - Todos      │
│ - Prompts    │ │ - Scheduling │ │ - Notifications│ │ - Tracking  │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│              MCP SERVER (local_mcp_server.py)              │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │  Tools:    │  │ Resources: │  │  Prompts:  │          │
│  │  - web_    │  │  - files   │  │  - system  │          │
│  │    search  │  │  - data    │  │    prompts │          │
│  │  - calc    │  │            │  │            │          │
│  │  - file_   │  │            │  │            │          │
│  │    reader  │  │            │  │            │          │
│  │  - image   │  │            │  │            │          │
│  │    gen     │  │            │  │            │          │
│  └────────────┘  └────────────┘  └────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND                                 │
│  - Streamlit (Web UI)                                      │
│  - Slack Bot API (Telegram optional)                       │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND                                  │
│  - Python 3.11+                                           │
│  - LangGraph (State Machine)                               │
│  - FastAPI (MCP Server)                                    │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                               │
│  - SQLite (mo11y_companion.db)                             │
│  - JSON (Config, Personas, RAGs)                          │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI/ML LAYER                              │
│  - Ollama (Local LLM)                                      │
│  - LangChain Core                                           │
│  - External APIs (HuggingFace, Google)                     │
└─────────────────────────────────────────────────────────────┘
```

## File Structure Overview

```
mo11y/
├── Core Agent
│   ├── mo11y_agent.py          # Main agent with LangGraph workflow
│   ├── enhanced_memory.py      # Multi-layered memory system
│   ├── companion_engine.py     # Personality evolution
│   └── relationship_timeline.py # Visualization tools
│
├── Services
│   ├── local_calendar.py       # Calendar management
│   ├── reminder_service.py     # Reminder system
│   ├── task_service.py         # Task management
│   └── life_journal.py         # Journal system
│
├── Integration
│   ├── mcp_integration.py      # MCP client
│   ├── local_mcp_server.py    # MCP server
│   ├── external_apis.py        # External API manager
│   └── conversation_logger.py  # Logging system
│
├── Interfaces
│   ├── app_enhanced.py         # Streamlit UI
│   └── slack_bot.py           # Slack integration (Telegram optional)
│
└── Configuration
    ├── config.json             # Main config
    ├── sonas/                  # Persona definitions
    └── RAGs/                   # RAG knowledge bases
```
