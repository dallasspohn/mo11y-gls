# Clear Streamlit Cache - Fix for Missing Method Error

## Issue

If you get an error like:
```
'Mo11yAgent' object has no attribute '_get_local_services_context'
```

This is because **Streamlit is caching an old version** of the agent that was created before the method was added.

## Solution

### Option 1: Clear Cache in Streamlit UI (Easiest)

1. In the Streamlit app, click the **"☰"** menu (top right)
2. Click **"Clear cache"**
3. Refresh the page
4. Try your message again

### Option 2: Restart Streamlit

```bash
# Stop Streamlit (Ctrl+C)
# Then restart
streamlit run app_enhanced.py
```

### Option 3: Clear Cache Programmatically

In `app_enhanced.py`, uncomment this line (around line 344):
```python
# get_agent.clear()
```

Change it to:
```python
get_agent.clear()  # Force cache clear
```

Then refresh the page. After it works, comment it out again.

### Option 4: Delete Cache Directory

```bash
# Streamlit cache is usually in:
rm -rf ~/.streamlit/cache/
# Or if using a venv:
rm -rf .streamlit/cache/
```

## Why This Happens

Streamlit uses `@st.cache_resource` to cache the agent instance. When you add new methods to the `Mo11yAgent` class, Streamlit doesn't automatically know to recreate the cached instance, so it uses the old one that doesn't have the new method.

## Prevention

The cache now includes a version parameter (`_cache_version: str = "v2.0"`). To force a refresh after code changes, increment the version number in `app_enhanced.py`:

```python
@st.cache_resource
def get_agent(sona_path_key: str = None, _cache_version: str = "v2.1"):  # Increment version
```

---

**Quick Fix**: Just restart Streamlit! 🚀
