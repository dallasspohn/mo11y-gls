# Mo11y - Your Open Source AI Business Assistant

A sophisticated, evolving AI business assistant built with LangGraph that grows and learns with you. Mo11y is designed as an open-source alternative to online chatbots, perfect for business use, Red Hat colleagues, and anyone who wants a private, customizable AI assistant.

## 🌟 Features

- **Long-term Memory**: Remembers your conversations, preferences, and important events
- **Task Management**: Set reminders, manage calendar events, and track tasks
- **Business Journal**: Builds a comprehensive timeline of your business activities through conversations
- **Natural Conversations**: Matches your tone and communication style
- **Privacy-First**: All data stays on your machine - no cloud dependencies
- **Extensible**: Built with LangGraph for easy customization and extension

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.ai/) installed and running
- DeepSeek R1 model (see [SETUP.md](SETUP.md) for installation)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mo11y-gls
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up DeepSeek R1 model** (see [SETUP.md](SETUP.md) for detailed instructions)
   ```bash
   ollama pull deepseek-r1:latest
   ```

4. **Start Ollama** (if not already running)
   ```bash
   ollama serve
   ```

5. **Run Mo11y**
   ```bash
   streamlit run app_enhanced.py
   ```

6. **Open your browser** to `http://localhost:8501`

That's it! Mo11y will create the database and start learning from your first conversation.

## 📖 Documentation

- **[SETUP.md](SETUP.md)** - Detailed setup instructions for DeepSeek R1
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture documentation
- **[COMMANDS.md](COMMANDS.md)** - Available commands reference

## 🎯 Core Capabilities

### Task Management
- Set reminders: "Remind me to call mom at 3pm"
- Calendar events: "Add a meeting tomorrow at 2pm"
- Task tracking: "What tasks do I have?"

### Memory & Learning
- Remembers your conversations
- Learns your preferences
- Builds a business journal over time
- Recalls past discussions when relevant

### Business Assistance
- Professional responses
- Helps process decisions logically
- Provides efficient business support

### Natural Conversation
- Matches your communication style
- Simple questions get simple answers
- Detailed when you need detail
- Casual when you're casual

## ⚙️ Configuration

Mo11y uses `config.json` for configuration. The default configuration works out of the box:

```json
{
    "sonas_dir": "./sonas/",
    "rags_dir": "./RAGs/",
    "db_path": "./mo11y_companion.db",
    "model_name": "deepseek-r1:latest"
}
```

### Key Settings

- `model_name`: The Ollama model to use (default: `deepseek-r1:latest`)
- `db_path`: Path to the SQLite database (default: `./mo11y_companion.db`)
- `sonas_dir`: Directory containing persona files (default: `./sonas/`)
- `rags_dir`: Directory containing RAG knowledge bases (default: `./RAGs/`)

## 🏗️ Architecture

Mo11y is built with:

- **LangGraph**: Stateful agent workflow
- **Streamlit**: Beautiful web interface
- **SQLite**: Local database for memories
- **Ollama**: Local LLM inference

```
┌─────────────────────────────────────────┐
│         Streamlit UI (app_enhanced.py)  │
└──────────────┬──────────────────────────┘
               │
       ┌───────▼────────┐
       │  Mo11y Agent   │
       │  (LangGraph)   │
       └───────┬────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐
│Memory │ │Persona│ │ Tools │
│System │ │Engine │ │ (MCP) │
└───────┘ └───────┘ └───────┘
    │          │          │
    └──────────┼──────────┘
               │
        ┌──────▼──────┐
        │ SQLite DB   │
        └─────────────┘
```

## 🔧 For Red Hat Colleagues

Mo11y is designed to be:
- **Self-hosted**: Run on your own machine
- **Customizable**: Easy to modify and extend
- **Private**: All data stays local
- **Open Source**: Contribute improvements back to the community

**Note**: For Red Hat employees, there is a companion repository that accompanies this one. The Red Hat content creation features automatically pull the latest standards from the `redhat-content-standards` repository when creating training content.

### Customization

- **Personas**: Create custom personas in `sonas/` directory
- **RAG Data**: Add knowledge bases in `RAGs/` directory
- **Tools**: Extend with MCP (Model Context Protocol) tools
- **UI**: Customize the Streamlit interface

## 🤝 Contributing

Contributions are welcome! Please feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## 📝 License

[Add your license here]

## 🙏 Acknowledgments

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [Streamlit](https://streamlit.io/)
- [Ollama](https://ollama.ai/)
- [DeepSeek](https://www.deepseek.com/)

## 💬 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check [SETUP.md](SETUP.md) for setup help
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for technical details

---

**Built for professional business use**

*Mo11y - Your AI business assistant that grows with you*
