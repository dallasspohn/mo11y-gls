# Mo11y Setup Guide - DeepSeek R1

This guide will walk you through setting up Mo11y with the DeepSeek R1 model.

## Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.ai/) installed
- Internet connection (for downloading the model)

## Step 1: Install Ollama

If you haven't already installed Ollama:

### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### macOS
Download from [ollama.ai](https://ollama.ai/download) or use Homebrew:
```bash
brew install ollama
```

### Windows
Download the installer from [ollama.ai](https://ollama.ai/download)

## Step 2: Start Ollama

Start the Ollama service:

```bash
ollama serve
```

Keep this terminal open. Ollama will run in the background.

## Step 3: Download DeepSeek R1 Model

In a new terminal, download the DeepSeek R1 model:

```bash
ollama pull deepseek-r1:latest
```

This will download the model (approximately 4-5 GB). The download may take a few minutes depending on your internet connection.

### Verify Installation

Check that the model is installed:

```bash
ollama list
```

You should see `deepseek-r1:latest` in the list.

### Test the Model

Test that the model works:

```bash
ollama run deepseek-r1:latest "Hello, can you introduce yourself?"
```

If you get a response, the model is working correctly!

## Step 4: Install Mo11y Dependencies

Navigate to the Mo11y directory and install dependencies:

```bash
cd mo11y-gls
pip install -r requirements.txt
```

### Optional: Virtual Environment (Recommended)

It's recommended to use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 5: Configure Mo11y

Mo11y comes with a default `config.json` that uses DeepSeek R1. Verify the configuration:

```json
{
    "sonas_dir": "./sonas/",
    "rags_dir": "./RAGs/",
    "db_path": "./mo11y_companion.db",
    "model_name": "deepseek-r1:latest"
}
```

The `model_name` should be set to `"deepseek-r1:latest"`. If you need to change it, edit `config.json`.

## Step 6: Start Mo11y

With Ollama running in one terminal, start Mo11y in another:

```bash
# If using virtual environment, activate it first:
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start Mo11y
streamlit run app_enhanced.py
```

Mo11y will:
- Create the database automatically
- Load the Mo11y persona
- Start the web interface

## Step 7: Access Mo11y

Open your browser and navigate to:

```
http://localhost:8501
```

You should see the Mo11y interface! Start chatting to begin building your relationship.

## Troubleshooting

### Model Not Found Error

**Error**: `model 'deepseek-r1:latest' not found`

**Solution**:
```bash
# Make sure Ollama is running
ollama serve

# Pull the model again
ollama pull deepseek-r1:latest

# Verify it's installed
ollama list | grep deepseek-r1
```

### Connection Refused Error

**Error**: `[Errno 111] Connection refused`

**Solution**:
```bash
# Check if Ollama is running
pgrep -x ollama

# If not, start it
ollama serve

# Or run in background
nohup ollama serve > /dev/null 2>&1 &
```

### Model Too Slow

**Solutions**:
1. Use a smaller DeepSeek variant (if available)
2. Ensure you have enough RAM (DeepSeek R1 needs ~8GB RAM)
3. Close other applications to free up resources

### Wrong Model Behavior

**Check**:
1. Verify model name in `config.json` matches `ollama list` output
2. Restart Streamlit after changing model
3. Clear browser cache if UI seems cached

### Database Creation Issues

If the database doesn't create automatically:

```bash
# Check write permissions in the directory
ls -la mo11y_companion.db

# Create database manually if needed
python3 -c "from enhanced_memory import EnhancedMemory; em = EnhancedMemory('mo11y_companion.db'); print('Database created')"
```

## Advanced Configuration

### Using a Different Model

To use a different model, edit `config.json`:

```json
{
    "model_name": "your-model-name:tag"
}
```

Then restart Streamlit.

### Custom Database Location

To use a custom database location:

```json
{
    "db_path": "/path/to/your/database.db"
}
```

### Environment Variables

You can override config.json using environment variables:

```bash
export MO11Y_MODEL_NAME="deepseek-r1:latest"
export MO11Y_DB_PATH="./my_database.db"
streamlit run app_enhanced.py
```

## Next Steps

Once Mo11y is running:

1. **Start a conversation** - Mo11y learns from every interaction
2. **Set reminders** - Try "Remind me to call mom at 3pm"
3. **Add calendar events** - Try "Add a meeting tomorrow at 2pm"
4. **Build your life journal** - Share memories and Mo11y will remember them
5. **Explore features** - Check out the sidebar for relationship stats and memory vault

## Getting Help

If you encounter issues:

1. Check this guide first
2. Review the [README.md](README.md) for general information
3. Check [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
4. Open an issue on GitHub with:
   - Your operating system
   - Python version (`python3 --version`)
   - Ollama version (`ollama --version`)
   - Error messages or logs

## Model Recommendations

While DeepSeek R1 is the default, Mo11y works with any Ollama model:

- **deepseek-r1:latest** - Default, excellent reasoning (recommended)
- **llama3.2:3b** - Fast, good for testing
- **qwen2.5:7b** - High quality responses
- **mistral:7b** - Good general purpose

To switch models, just change `model_name` in `config.json` and restart Streamlit.

---

**Happy chatting with Mo11y! 💝**
