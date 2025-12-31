# Mo11y Commands Reference

This file lists all available commands you can use in the chat interface.

## Command Format

Commands start with `/` followed by the command name. Some commands accept additional parameters.

## Available Commands

### `/journal` - Journal Entry
**Usage:** `/journal <your journal entry text>`

Automatically saves your message as a journal entry. The system will:
- Recognize it as a journal entry (not a regular chat message)
- Save it to the life journal system
- Tag it appropriately for future retrieval
- Store it in the database for better organization

**Example:**
```
/journal Today I went to the park with Blake. He's really enjoying school.
```

**Note:** Journal entries are saved to `life-journal.json` only (not the database). This makes them simpler to track, edit, and backup over time. The file is human-readable JSON and easy to manage.

---

### `/tool-builder` - Switch to Tool Builder Persona
**Usage:** `/tool-builder`

Switches to the Tool Builder persona, which helps you create MCP tools. After switching, you can ask Tool Builder to create tools and they will be automatically created.

**Bonus:** When you use `/tool-builder`, you'll see a numbered list of all available MCP tools before switching!

**Example:**
```
/tool-builder
Create a tool that searches my-life.json for a word
```

---

### `/alex` - Switch to Alex Mercer Persona
**Usage:** `/alex`

Switches to the Alex Mercer persona (your personal assistant).

---

### `/izzy` - Switch to Izzy-Chan Persona
**Usage:** `/izzy`

Switches to the Izzy-Chan persona (sassy & flirtatious).

---

### `/cjs` - Switch to CJS (Jim) Persona
**Usage:** `/cjs`

Switches to the CJS persona (your father Jim).

---

### `/mo11y` - Switch to Mo11y Persona
**Usage:** `/mo11y`

Switches to the default Mo11y persona (your lifelong companion).

---

### `/help` or `/commands` - Show Commands Help
**Usage:** `/help` or `/commands`

Displays the full COMMANDS.md file with all available commands and their usage.

**Note:** You can also ask naturally: "show me COMMANDS.md" or "what commands are available" and the system will display this file.

---

## Command Behavior

- Commands are case-insensitive (`/journal` = `/Journal` = `/JOURNAL`)
- Commands must be at the start of your message
- After a command executes, the remaining text (if any) is processed normally
- Some commands switch personas, which changes the conversation context

## Future Commands

More commands will be added over time. Check this file for updates!
