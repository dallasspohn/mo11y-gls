"""
Conversation Logger for Mo11y Agent
Logs conversations with detailed metadata about data sources used
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class ConversationLogger:
    """
    Logs conversations with metadata about:
    - User input and agent response
    - Memories retrieved (episodic, semantic, related)
    - RAG data used
    - Life journal entries referenced
    - External API calls
    - MCP tool usage
    - Personality context
    """
    
    def __init__(self, log_dir: str = "conversation_logs", persona_name: str = "default"):
        """
        Initialize conversation logger
        
        Args:
            log_dir: Directory to store log files
            persona_name: Name of persona (used in filename)
        """
        self.log_dir = log_dir
        self.persona_name = persona_name.replace(" ", "_").lower()
        self.conversation_count = 0
        
        # Create log directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(
            self.log_dir, 
            f"{self.persona_name}_conversation_{timestamp}.txt"
        )
        
        # Initialize log file with header
        self._write_header()
    
    def _write_header(self):
        """Write header to log file"""
        header = f"""
{'='*80}
Conversation Log: {self.persona_name.upper()}
Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{'='*80}

This log contains detailed information about each conversation exchange,
including what data sources were used to generate responses.

Format:
- Exchange #N: User input and agent response
- Data Sources: What information was retrieved/used
- Context: Additional context provided to the model

{'='*80}

"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(header)
    
    def log_exchange(
        self,
        user_input: str,
        agent_response: str,
        state: Dict,
        metadata: Optional[Dict] = None
    ):
        """
        Log a conversation exchange with full context
        
        Args:
            user_input: User's message
            agent_response: Agent's response
            state: Full agent state after processing
            metadata: Additional metadata (persona name, model used, etc.)
        """
        self.conversation_count += 1
        
        # Extract data sources from state
        memories_retrieved = state.get("memories_retrieved", {})
        context = state.get("context", {})
        personality_context = state.get("personality_context", "")
        
        # Build log entry
        log_entry = f"""
{'='*80}
EXCHANGE #{self.conversation_count}
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{'='*80}

USER INPUT:
{user_input}

{'='*80}
AGENT RESPONSE:
{agent_response}

{'='*80}
DATA SOURCES USED:
"""
        
        # Episodic memories
        episodic_memories = memories_retrieved.get("episodic", [])
        if episodic_memories:
            log_entry += f"\nEPISODIC MEMORIES ({len(episodic_memories)} retrieved):\n"
            for i, mem in enumerate(episodic_memories[:5], 1):  # Limit to 5
                log_entry += f"  {i}. [{mem.get('timestamp', 'Unknown')}] "
                log_entry += f"Importance: {mem.get('importance_score', 0):.2f}\n"
                log_entry += f"     Content: {mem.get('content', '')[:200]}...\n"
                log_entry += f"     Tags: {', '.join(mem.get('tags', []))}\n"
        else:
            log_entry += "\nEPISODIC MEMORIES: None retrieved\n"
        
        # Semantic memories
        semantic_memories = memories_retrieved.get("semantic", {})
        if semantic_memories:
            log_entry += f"\nSEMANTIC MEMORIES ({len(semantic_memories)} retrieved):\n"
            for key, value in list(semantic_memories.items())[:5]:  # Limit to 5
                if isinstance(value, dict):
                    log_entry += f"  - {key}: {value.get('value', '')[:150]}...\n"
                else:
                    log_entry += f"  - {key}: {str(value)[:150]}...\n"
        else:
            log_entry += "\nSEMANTIC MEMORIES: None retrieved\n"
        
        # Related memories
        related_memories = memories_retrieved.get("related", [])
        if related_memories:
            log_entry += f"\nRELATED MEMORIES ({len(related_memories)} retrieved):\n"
            for i, mem in enumerate(related_memories[:3], 1):  # Limit to 3
                log_entry += f"  {i}. [{mem.get('id', 'Unknown')}] "
                log_entry += f"Importance: {mem.get('importance_score', 0):.2f}\n"
                log_entry += f"     Content: {mem.get('content', '')[:150]}...\n"
        else:
            log_entry += "\nRELATED MEMORIES: None retrieved\n"
        
        # RAG data (check if used)
        log_entry += "\nRAG DATA:\n"
        data_sources = state.get("data_sources", {})
        rag_files = data_sources.get("rag_files", [])
        if rag_files:
            log_entry += f"  RAG files loaded: {', '.join(rag_files)}\n"
        elif hasattr(self, '_rag_used') and self._rag_used:
            log_entry += f"  RAG files loaded: {', '.join(self._rag_used)}\n"
        else:
            log_entry += "  RAG data: None used\n"
        
        # Life journal (check if used)
        log_entry += "\nLIFE JOURNAL:\n"
        life_journal_entries = data_sources.get("life_journal_entries", [])
        if life_journal_entries:
            log_entry += f"  Life journal entries referenced ({len(life_journal_entries)}):\n"
            for entry in life_journal_entries[:5]:  # Limit to 5
                log_entry += f"    - {entry}\n"
        elif hasattr(self, '_life_journal_used') and self._life_journal_used:
            log_entry += f"  Life journal entries referenced ({len(self._life_journal_used)}):\n"
            for entry in self._life_journal_used[:5]:
                log_entry += f"    - {entry}\n"
        else:
            log_entry += "  Life journal: None used\n"
        
        # Local Services (Calendar, Reminders, Tasks)
        log_entry += "\nLOCAL SERVICES:\n"
        local_services = data_sources.get("local_services", {})
        if local_services:
            calendar_events = local_services.get("calendar_events", [])
            reminders = local_services.get("reminders", [])
            tasks = local_services.get("tasks", [])
            overdue_tasks = local_services.get("overdue_tasks", [])
            
            if calendar_events:
                log_entry += f"  Calendar Events ({len(calendar_events)} retrieved):\n"
                for event in calendar_events[:5]:
                    log_entry += f"    - {event.get('title', 'Event')} on {event.get('start_time', 'Unknown')}\n"
            if reminders:
                log_entry += f"  Reminders ({len(reminders)} retrieved):\n"
                for reminder in reminders[:5]:
                    log_entry += f"    - {reminder.get('title', 'Reminder')} (due: {reminder.get('reminder_time', 'Unknown')})\n"
            if tasks:
                log_entry += f"  Tasks ({len(tasks)} retrieved):\n"
                for task in tasks[:5]:
                    importance = task.get('importance', 5)
                    priority = task.get('priority', 'medium')
                    title = task.get('title', 'Task')
                    due_date = task.get('due_date', '')
                    due_str = f" (due: {due_date})" if due_date else ""
                    log_entry += f"    - [{priority.upper()}] Importance: {importance}/10 - {title}{due_str}\n"
            if overdue_tasks:
                log_entry += f"  Overdue Tasks ({len(overdue_tasks)} retrieved):\n"
                for task in overdue_tasks[:3]:
                    importance = task.get('importance', 5)
                    title = task.get('title', 'Task')
                    due_date = task.get('due_date', 'Unknown')
                    log_entry += f"    - Importance: {importance}/10 - {title} (was due: {due_date})\n"
            
            bills = local_services.get("bills", [])
            overdue_bills = local_services.get("overdue_bills", [])
            if bills:
                log_entry += f"  Bills ({len(bills)} retrieved):\n"
                for bill in bills[:5]:
                    name = bill.get('name', 'Bill')
                    amount = bill.get('amount', 0)
                    importance = bill.get('importance', 5)
                    due_date = bill.get('due_date', 'Unknown')
                    category = bill.get('category', '')
                    category_str = f" [{category}]" if category else ""
                    log_entry += f"    - Importance: {importance}/10 - {name}{category_str}: ${amount:.2f} (due: {due_date})\n"
            if overdue_bills:
                log_entry += f"  Overdue Bills ({len(overdue_bills)} retrieved):\n"
                for bill in overdue_bills[:3]:
                    name = bill.get('name', 'Bill')
                    amount = bill.get('amount', 0)
                    importance = bill.get('importance', 5)
                    due_date = bill.get('due_date', 'Unknown')
                    log_entry += f"    - Importance: {importance}/10 - {name}: ${amount:.2f} (was due: {due_date})\n"
            
            if not any([calendar_events, reminders, tasks, overdue_tasks, bills, overdue_bills]):
                log_entry += "  Local Services: None used\n"
        else:
            log_entry += "  Local Services: None used\n"
        
        # External APIs
        log_entry += "\nEXTERNAL APIS:\n"
        if context.get("has_media"):
            log_entry += f"  Media files: {len(context.get('media_files', []))}\n"
        else:
            log_entry += "  External APIs: None used\n"
        
        # MCP Tools
        log_entry += "\nMCP TOOLS:\n"
        mcp_tools = data_sources.get("mcp_tools", [])
        if mcp_tools:
            log_entry += f"  Tools used ({len(mcp_tools)}):\n"
            for tool in mcp_tools:
                log_entry += f"    - {tool}\n"
        elif hasattr(self, '_mcp_tools_used') and self._mcp_tools_used:
            log_entry += f"  Tools used ({len(self._mcp_tools_used)}):\n"
            for tool in self._mcp_tools_used:
                log_entry += f"    - {tool}\n"
        else:
            log_entry += "  MCP Tools: None used\n"
        
        # Context information
        log_entry += f"\n{'='*80}\nCONTEXT INFORMATION:\n{'='*80}\n"
        log_entry += f"Topics extracted: {', '.join(context.get('topics', []))}\n"
        log_entry += f"User sentiment: {state.get('user_sentiment', 0.0):.2f}\n"
        log_entry += f"Has question: {context.get('has_question', False)}\n"
        log_entry += f"Has exclamation: {context.get('has_exclamation', False)}\n"
        
        # Personality context (truncated)
        if personality_context:
            log_entry += f"\nPersonality context length: {len(personality_context)} chars\n"
            log_entry += f"Personality context preview:\n{personality_context[:500]}...\n"
        
        # Metadata
        if metadata:
            log_entry += f"\n{'='*80}\nMETADATA:\n{'='*80}\n"
            for key, value in metadata.items():
                log_entry += f"{key}: {value}\n"
        
        log_entry += f"\n{'='*80}\n\n"
        
        # Write to file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        # Also write to a summary file (last 30 exchanges)
        self._update_summary(user_input, agent_response, memories_retrieved)
    
    def _update_summary(self, user_input: str, agent_response: str, memories_retrieved: Dict):
        """Update a summary file with just the last 30 exchanges"""
        summary_file = self.log_file.replace('.txt', '_summary.txt')
        
        # Read existing summary if it exists
        exchanges = []
        if os.path.exists(summary_file):
            with open(summary_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract exchange count from content
                if 'EXCHANGE #' in content:
                    # Count existing exchanges
                    exchange_count = content.count('EXCHANGE #')
                    if exchange_count >= 30:
                        # Keep only last 30
                        lines = content.split('\n')
                        # Find where exchange 1 starts (after header)
                        start_idx = 0
                        for i, line in enumerate(lines):
                            if 'EXCHANGE #' in line and 'EXCHANGE #1' in line:
                                start_idx = i
                                break
                        # Keep header + last 30 exchanges
                        header_lines = lines[:start_idx]
                        exchange_lines = lines[start_idx:]
                        # Rebuild with last 30
                        content = '\n'.join(header_lines + exchange_lines[-1000:])  # Approximate
        
        # Add new exchange
        exchange_text = f"""
EXCHANGE #{self.conversation_count}
USER: {user_input}
AGENT: {agent_response}
MEMORIES: {len(memories_retrieved.get('episodic', []))} episodic, {len(memories_retrieved.get('semantic', {}))} semantic
---
"""
        
        with open(summary_file, 'a', encoding='utf-8') as f:
            if not os.path.exists(summary_file) or os.path.getsize(summary_file) == 0:
                f.write(f"Summary: Last 30 exchanges for {self.persona_name}\n{'='*80}\n")
            f.write(exchange_text)
    
    def get_log_file_path(self) -> str:
        """Get the path to the current log file"""
        return self.log_file
    
    def get_summary_file_path(self) -> str:
        """Get the path to the summary file"""
        return self.log_file.replace('.txt', '_summary.txt')
    
    def log_data_source(self, source_type: str, details: str):
        """Log additional data source information"""
        # Store for next exchange
        if not hasattr(self, '_data_sources'):
            self._data_sources = []
        self._data_sources.append(f"{source_type}: {details}")
    
    def set_rag_used(self, rag_files: List[str]):
        """Mark which RAG files were used"""
        self._rag_used = rag_files
    
    def set_life_journal_used(self, entries: List[str]):
        """Mark which life journal entries were used"""
        self._life_journal_used = entries
    
    def set_mcp_tools_used(self, tools: List[str]):
        """Mark which MCP tools were used"""
        self._mcp_tools_used = tools
