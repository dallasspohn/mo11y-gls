# Persona Switcher Guide

## Overview

The persona switcher has been added to the left sidebar of `app_enhanced.py`. You can now easily switch between all available personas (sonas) without restarting the app!

## How to Use

1. **Open the app**: Run `streamlit run app_enhanced.py`
2. **Find the Persona Selector**: Look at the top of the left sidebar - you'll see "🎭 Select Persona"
3. **Choose a persona**: Click the dropdown to see all available personas
4. **Switch**: Select any persona - the agent will automatically reload with the new persona

## Available Personas

The switcher automatically discovers all `.json` files in your `sonas/` directory. Currently available personas include:

- **Mo11y** - Your lifelong companion who grows with you
- Create your own custom personas by adding JSON files to the `sonas/` directory

## Features

### Dynamic Loading
- Automatically scans the `sonas/` directory for all `.json` persona files
- Shows persona name from the JSON file (or generates one from filename)
- Displays persona description in an expandable section

### Smart Caching
- Agent is cached per persona for performance
- When you switch personas, the cache is cleared and the agent reloads
- Each persona maintains its own personality and memory context

### Visual Feedback
- Persona name and icon displayed at the top of sidebar
- Description available in expandable section
- Chat page title updates to reflect selected persona

## How It Works

1. **Discovery**: `get_available_sonas()` scans the sonas directory
2. **Selection**: Dropdown shows all available personas + "None (Default)"
3. **Loading**: When selected, the agent is initialized with the chosen sona file
4. **Caching**: Agent is cached by persona path, so switching back is instant

## Adding New Personas

To add a new persona:

1. Create a JSON file in the `sonas/` directory
2. Follow the structure of existing sona files:
   ```json
   {
     "name": "Your Persona Name",
     "description": "What this persona is like",
     "personality": {
       "tone": "...",
       "humor": "...",
       ...
     }
   }
   ```
3. The persona will automatically appear in the dropdown!

## Technical Details

- **Function**: `get_available_sonas()` - Scans and loads all sona files
- **Caching**: `@st.cache_resource` with persona path as key
- **Session State**: `selected_persona` tracks current selection
- **Auto-reload**: When persona changes, `get_agent.clear()` is called and `st.rerun()` refreshes the app

## Troubleshooting

### Persona Not Appearing
- Check that the JSON file is valid JSON
- Ensure the file ends with `.json`
- Verify the file is in the `sonas/` directory (check `config.json` for path)

### Agent Not Changing
- The agent cache is cleared when switching - if it doesn't change, try refreshing the page
- Check that the sona file has a valid structure

### Default Persona
- Select "None (Default)" to use the agent without any persona file
- This uses the base personality traits without a specific sona

## Enjoy Exploring!

Try switching between different personas to see how they respond differently to the same questions. Each persona brings its own personality, tone, and style to the conversation!
