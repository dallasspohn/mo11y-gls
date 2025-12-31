# Conversation Logging Guide

## Overview

Mo11y now includes detailed conversation logging that tracks every exchange and records what data sources were used to generate responses. This is especially useful for debugging persona behavior and understanding where information is being pulled from.

## What Gets Logged

For each conversation exchange, the logger records:

1. **User Input**: The exact message you sent
2. **Agent Response**: The complete response from the agent
3. **Episodic Memories**: Which specific memories were retrieved (with timestamps, importance scores, tags)
4. **Semantic Memories**: Facts and knowledge that were recalled
5. **Related Memories**: Memories linked to the current topic
6. **RAG Data**: Which RAG files were loaded and used
7. **Life Journal**: Which life journal entries were referenced
8. **MCP Tools**: Which tools were called (web search, etc.)
9. **Context Information**: Topics extracted, sentiment, personality context

## Log Files

Logs are stored in the `conversation_logs/` directory with the following naming:

- **Full log**: `{persona_name}_conversation_{timestamp}.txt`
- **Summary log**: `{persona_name}_conversation_{timestamp}_summary.txt`

The summary file contains just the last 30 exchanges in a condensed format.

## Example Log Entry

```
================================================================================
EXCHANGE #1
Timestamp: 2025-01-15 14:30:22
================================================================================

USER INPUT:
Tell me about my dad's shop

================================================================================
AGENT RESPONSE:
Your dad, Jim, ran Jim's Prop Shop in Crandall, TX...

================================================================================
DATA SOURCES USED:

EPISODIC MEMORIES (3 retrieved):
  1. [2025-01-10 10:15:00] Importance: 0.85
     Content: User mentioned Jim's Prop Shop...
     Tags: ['family', 'business', 'dad']

SEMANTIC MEMORIES (2 retrieved):
  - user_father_name: Jim
  - user_father_business: Jim's Prop Shop

RAG DATA:
  RAG files loaded: cjs.json, Clark_rag.json

LIFE JOURNAL:
  Life journal entries referenced (2):
    - Timeline[1985]: Jim opened Jim's Prop Shop...
    - Friend: Jim

MCP TOOLS:
  MCP Tools: None used

================================================================================
CONTEXT INFORMATION:
================================================================================
Topics extracted: dad, shop, business
User sentiment: 0.30
Has question: False
Has exclamation: False
```

## Using Logs for Debugging

After having ~30 conversations with a persona (like CJS), you can:

1. **Find the log file**: Check `conversation_logs/` directory
2. **Review the summary**: Look at `*_summary.txt` for a quick overview
3. **Share with me**: Send the log file and tell me:
   - What responses were wrong/unexpected
   - Where you expected the persona to pull data from
   - What data sources it should have used instead

## Log File Location

The log file path is returned in the chat response:

```python
result = agent.chat("Hello")
log_file = result.get("log_file")  # Path to log file
```

You can also find it in the `conversation_logs/` directory.

## Disabling Logging

To disable logging, set `enable_logging=False` when creating the agent:

```python
agent = create_mo11y_agent(
    sona_path="sonas/cjs.json",
    enable_logging=False
)
```

Or in the Streamlit app, it's enabled by default but can be disabled in the code.

## Tips

- **Review regularly**: Check logs after every 20-30 exchanges to catch issues early
- **Compare sources**: Look at what data sources were used vs. what should have been used
- **Check RAG loading**: Verify that the correct RAG files are being loaded
- **Life journal entries**: See if the right journal entries are being referenced
- **Memory relevance**: Check if the right memories are being retrieved based on topics

## Example: Debugging CJS Persona

If CJS is giving wrong information about your dad:

1. Check the log to see which RAG files were loaded
2. Verify if `cjs.json` or `Clark_rag.json` were used
3. Check if life journal entries about Jim were referenced
4. See if episodic memories about your dad were retrieved
5. Compare what was used vs. what should have been used

This will help identify:
- Wrong RAG files being loaded
- Life journal entries not being found
- Memories not being retrieved correctly
- Context not being passed to the model properly
