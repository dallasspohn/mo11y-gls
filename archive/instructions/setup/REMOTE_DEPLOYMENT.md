# Remote Deployment Configuration Guide

## Problem
When the agent runs on a **separate computer** (remote server), the configuration is pointing to:
- `localhost:8443` - This refers to the **local PC**, not the remote server
- Hardcoded paths like `/home/dallas/dev/mo11y/` - These paths exist on the **local PC**, not the remote server

## Solution

### 1. Update `config.json` for Remote Server

When deploying on a remote server, you need to configure paths and URLs relative to **where the agent is actually running**.

#### Option A: Use Relative Paths (Recommended)
```json
{
    "sonas_dir": "./sonas/",
    "rags_dir": "./RAGs/",
    "db_path": "./SPOHNZ.db",
    "model_name": "Izzy-Chan:latest",
    "suppress_thinking": true,
    "mcp_server_url": "http://localhost:8443"
}
```

**Note**: `mcp_server_url` should point to `localhost:8443` **on the remote server** (where the MCP server is running), not your local PC.

#### Option B: Use Environment Variables
Set these on the remote server:
```bash
export MO11Y_SONAS_DIR="/path/on/remote/server/sonas/"
export MO11Y_RAGS_DIR="/path/on/remote/server/RAGs/"
export MO11Y_DB_PATH="/path/on/remote/server/SPOHNZ.db"
export MCP_SERVER_URL="http://localhost:8443"
```

Then use relative paths in `config.json` (the code will check environment variables first).

### 2. MCP Server Configuration

The MCP server should run **on the remote server** where the agent is running.

**On the remote server:**
```bash
# Start MCP server
python3 local_mcp_server.py

# It will run on http://localhost:8443 (on the remote server)
```

**In config.json on remote server:**
```json
{
    "mcp_server_url": "http://localhost:8443"
}
```

This `localhost` refers to the **remote server**, not your local PC.

### 3. If MCP Server Runs on Different Machine

If the MCP server runs on a different machine than the agent:

**On the remote server (where agent runs):**
```json
{
    "mcp_server_url": "http://192.168.1.XXX:8443"
}
```

Replace `192.168.1.XXX` with the actual IP address of the machine running the MCP server.

### 4. File Paths

All file paths in `config.json` should be relative to **where the agent is running**:

- ✅ **Correct** (relative paths): `"./sonas/"`, `"./RAGs/", "./SPOHNZ.db"`
- ✅ **Correct** (absolute paths on remote): `"/home/user/mo11y/sonas/"`
- ❌ **Wrong** (local PC paths): `"/home/dallas/dev/mo11y/sonas/"`

### 5. Database Path

The database file (`db_path`) should be on the **remote server**:

```json
{
    "db_path": "./SPOHNZ.db"  // Relative to where agent runs
}
```

Or absolute path on remote server:
```json
{
    "db_path": "/home/user/mo11y/SPOHNZ.db"
}
```

## Quick Setup Checklist

### On Remote Server:
- [ ] Copy all files to remote server (including `sonas/`, `RAGs/`, etc.)
- [ ] Update `config.json` with paths relative to remote server location
- [ ] Set `mcp_server_url` to `http://localhost:8443` (refers to remote server)
- [ ] Start MCP server on remote server: `python3 local_mcp_server.py`
- [ ] Verify MCP server is running: `curl http://localhost:8443/health` (on remote server)
- [ ] Start agent on remote server

### On Local PC:
- [ ] If accessing agent remotely, use SSH tunnel or remote URL
- [ ] Don't use paths from local PC in remote config

## Example: Remote Server Setup

**Remote server IP**: `192.168.1.100`
**Remote server user**: `user`
**Remote server path**: `/home/user/mo11y/`

**config.json on remote server:**
```json
{
    "sonas_dir": "/home/user/mo11y/sonas/",
    "rags_dir": "/home/user/mo11y/RAGs/",
    "db_path": "/home/user/mo11y/SPOHNZ.db",
    "model_name": "Izzy-Chan:latest",
    "suppress_thinking": true,
    "mcp_server_url": "http://localhost:8443"
}
```

**On remote server:**
```bash
cd /home/user/mo11y
python3 local_mcp_server.py  # Runs on localhost:8443 (remote server)
# In another terminal:
streamlit run app_enhanced.py  # Agent connects to localhost:8443 (remote server)
```

## Troubleshooting

### "Connection refused" to MCP server
- **Problem**: Agent can't connect to MCP server
- **Solution**: Make sure MCP server is running **on the remote server** where agent runs
- **Check**: `curl http://localhost:8443/health` (run this **on the remote server**)

### File not found errors
- **Problem**: Agent can't find `sonas/`, `RAGs/`, or database files
- **Solution**: Update paths in `config.json` to point to files **on the remote server**
- **Check**: `ls -la /path/in/config.json` (run this **on the remote server**)

### Database errors
- **Problem**: Can't access database file
- **Solution**: Ensure `db_path` in `config.json` points to database **on the remote server**
- **Check**: Database file exists and is readable on remote server

## Summary

**Key Point**: When the agent runs on a remote server:
- All paths in `config.json` should be relative to **the remote server**
- `localhost` in `mcp_server_url` refers to **the remote server**, not your local PC
- All files (sonas, RAGs, database) must exist **on the remote server**
