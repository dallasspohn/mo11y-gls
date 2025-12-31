# Mo11y Quick Start Guide

Get Mo11y up and running in 5 minutes!

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed

## Steps

1. **Install Ollama** (if not already installed)
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Start Ollama**
   ```bash
   ollama serve
   ```

3. **Download DeepSeek R1**
   ```bash
   ollama pull deepseek-r1:latest
   ```

4. **Install Mo11y dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Copy config template**
   ```bash
   cp config.json.example config.json
   ```

6. **Start Mo11y**
   ```bash
   streamlit run app_enhanced.py
   ```

7. **Open browser**
   ```
   http://localhost:8501
   ```

That's it! Start chatting with Mo11y.

## Need Help?

- See [SETUP.md](SETUP.md) for detailed setup instructions
- See [README.md](README.md) for full documentation
- Check [TROUBLESHOOTING.md](SETUP.md#troubleshooting) for common issues

---

**Happy chatting! 💝**
