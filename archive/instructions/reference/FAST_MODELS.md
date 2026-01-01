# Fast Model Recommendations for Mo11y

## Current Issue
`deepseek-r1:latest` is a large reasoning model (7B+ parameters) which can be slow, especially on CPU or limited GPU.

## Fast Model Options

### Tier 1: Very Fast (1-3B models) ⚡⚡⚡
**Best for: Quick responses, testing, lower resource usage**

1. **llama3.2:1b** - Ultra fast, good for quick chats
   ```bash
   ollama pull llama3.2:1b
   ```
   - Speed: ⚡⚡⚡⚡⚡
   - Quality: ⭐⭐⭐
   - RAM: ~1GB

2. **phi3:mini** - Microsoft's efficient model
   ```bash
   ollama pull phi3:mini
   ```
   - Speed: ⚡⚡⚡⚡
   - Quality: ⭐⭐⭐⭐
   - RAM: ~2GB

3. **qwen2.5:0.5b** - Tiny but capable
   ```bash
   ollama pull qwen2.5:0.5b
   ```
   - Speed: ⚡⚡⚡⚡⚡
   - Quality: ⭐⭐⭐
   - RAM: ~500MB

### Tier 2: Balanced (3-7B models) ⚡⚡⚡⚡
**Best for: Good balance of speed and quality**

1. **llama3.2:3b** - Excellent balance ⭐ RECOMMENDED
   ```bash
   ollama pull llama3.2:3b
   ```
   - Speed: ⚡⚡⚡⚡
   - Quality: ⭐⭐⭐⭐
   - RAM: ~2GB
   - **Best overall choice for speed/quality**

2. **qwen2.5:1.5b** - Very fast, good quality
   ```bash
   ollama pull qwen2.5:1.5b
   ```
   - Speed: ⚡⚡⚡⚡⚡
   - Quality: ⭐⭐⭐⭐
   - RAM: ~1GB

3. **mistral:7b-instruct** - Fast 7B model
   ```bash
   ollama pull mistral:7b-instruct
   ```
   - Speed: ⚡⚡⚡
   - Quality: ⭐⭐⭐⭐⭐
   - RAM: ~4GB

### Tier 3: Faster DeepSeek Alternatives
**If you want DeepSeek quality but faster:**

1. **deepseek-r1:1.5b** - Smaller DeepSeek reasoning model
   ```bash
   ollama pull deepseek-r1:1.5b
   ```
   - Speed: ⚡⚡⚡⚡
   - Quality: ⭐⭐⭐⭐
   - RAM: ~1GB

2. **deepseek-coder:1.3b** - Fast coding-focused model
   ```bash
   ollama pull deepseek-coder:1.3b
   ```
   - Speed: ⚡⚡⚡⚡
   - Quality: ⭐⭐⭐⭐
   - RAM: ~1GB

## Quick Switch Guide

### Step 1: Pull the model
```bash
ollama pull llama3.2:3b
```

### Step 2: Update config.json
```json
{
    "model_name": "llama3.2:3b"
}
```

### Step 3: Restart Streamlit
```bash
# Stop current instance (Ctrl+C)
streamlit run app_enhanced.py
```

## Speed Comparison (Approximate)

| Model | Response Time | Quality | RAM |
|-------|--------------|---------|-----|
| deepseek-r1:latest | 10-30s | ⭐⭐⭐⭐⭐ | ~8GB |
| llama3.2:3b | 2-5s | ⭐⭐⭐⭐ | ~2GB |
| llama3.2:1b | 1-3s | ⭐⭐⭐ | ~1GB |
| phi3:mini | 2-4s | ⭐⭐⭐⭐ | ~2GB |
| qwen2.5:1.5b | 1-3s | ⭐⭐⭐⭐ | ~1GB |

## Recommendations by Use Case

### For Alex Mercer (Financial/Life Coaching)
- **Best:** `llama3.2:3b` or `mistral:7b-instruct`
- **Reason:** Good reasoning, fast enough for conversations

### For Quick Testing
- **Best:** `llama3.2:1b` or `qwen2.5:0.5b`
- **Reason:** Very fast, good enough for testing

### For Best Speed/Quality Balance
- **Best:** `llama3.2:3b` ⭐
- **Reason:** Excellent balance, widely used

### For Maximum Speed
- **Best:** `llama3.2:1b`
- **Reason:** Fastest while still being useful

## Check Available Models

```bash
# List all installed models
ollama list

# Test a model speed
time ollama run llama3.2:3b "Hello, how are you?"
```

## Performance Tips

1. **Use smaller models** - 1-3B models are much faster
2. **Use quantized versions** - Models with `:q4_0` or `:q8_0` suffix are faster
3. **Check GPU availability** - GPU is much faster than CPU
4. **Reduce context window** - Smaller context = faster responses

## Current Recommendation

**Switch to `llama3.2:3b`** - It's fast, high quality, and perfect for Mo11y conversations.

```bash
ollama pull llama3.2:3b
```

Then update config.json:
```json
{
    "model_name": "llama3.2:3b"
}
```
