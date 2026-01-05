"""
Mo11y Agent - LangGraph-based companion agent
A stateful, evolving AI companion that grows with you
"""

from typing import TypedDict, List, Dict, Optional
import json
import os
import re
from datetime import datetime

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("Warning: LangGraph not available. Install with: pip install langgraph")

from enhanced_memory import EnhancedMemory
from companion_engine import CompanionPersonality
from ollama import chat
from journal import Journal
from external_apis import ExternalAPIManager
from mcp_integration import MCPClient, MCPToolExecutor, DockerMCPServer
from conversation_logger import ConversationLogger
from local_calendar import LocalCalendar
from reminder_service import ReminderService
from task_service import TaskService
from financial_service import FinancialService

# Import CJS conversation updater and quest system if available
try:
    import importlib.util
    import os
    updater_path = os.path.join(os.path.dirname(__file__), "sonas", "cjs_conversation_updater.py")
    if os.path.exists(updater_path):
        spec = importlib.util.spec_from_file_location("cjs_conversation_updater", updater_path)
        cjs_updater_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cjs_updater_module)
        CJSConversationUpdater = cjs_updater_module.CJSConversationUpdater
        CJS_UPDATER_AVAILABLE = True
    else:
        CJS_UPDATER_AVAILABLE = False
    
    # Try to load quest system
    quest_path = os.path.join(os.path.dirname(__file__), "sonas", "jim_quest_system.py")
    if os.path.exists(quest_path):
        spec = importlib.util.spec_from_file_location("jim_quest_system", quest_path)
        quest_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(quest_module)
        JimQuestSystem = quest_module.JimQuestSystem
        QUEST_SYSTEM_AVAILABLE = True
    else:
        QUEST_SYSTEM_AVAILABLE = False
    
    # Try to load Alex conversation updater
    alex_updater_path = os.path.join(os.path.dirname(__file__), "sonas", "alex_conversation_updater.py")
    if os.path.exists(alex_updater_path):
        spec = importlib.util.spec_from_file_location("alex_conversation_updater", alex_updater_path)
        alex_updater_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(alex_updater_module)
        AlexConversationUpdater = alex_updater_module.AlexConversationUpdater
        ALEX_UPDATER_AVAILABLE = True
    else:
        ALEX_UPDATER_AVAILABLE = False
except Exception as e:
    CJS_UPDATER_AVAILABLE = False
    QUEST_SYSTEM_AVAILABLE = False
    ALEX_UPDATER_AVAILABLE = False
    # Silently fail - updater is optional


class AgentState(TypedDict):
    """State that flows through the agent graph"""
    messages: List[Dict]
    user_input: str
    user_sentiment: float
    context: Dict
    memories_retrieved: Dict
    personality_context: str
    response: str
    should_proact: bool
    proactivity_suggestions: List[str]
    interaction_metadata: Dict


class Mo11yAgent:
    """
    LangGraph-based companion agent that:
    - Retrieves relevant memories
    - Adapts personality based on interactions
    - Generates contextual responses
    - Proactively engages
    """
    
    def __init__(self, model_name: str = "deepseek-r1:latest", 
                 db_path: str = "mo11y_companion.db",
                 sona_path: Optional[str] = None,
                 enable_mcp: bool = True,
                 enable_external_apis: bool = True,
                 suppress_thinking: bool = True,
                 rags_dir: Optional[str] = None,
                 enable_logging: bool = True):
        # Validate and sanitize model_name
        if not model_name or not isinstance(model_name, str) or not model_name.strip():
            raise ValueError(
                f"Invalid model_name: '{model_name}'. "
                f"Model name must be a non-empty string. "
                f"Please check your config.json file."
            )
        self.model_name = model_name.strip()
        self.suppress_thinking = suppress_thinking
        self.sona_path = sona_path
        self.memory = EnhancedMemory(db_path)
        self.personality = CompanionPersonality(db_path, sona_path)
        self.rags_dir = rags_dir
        self.rag_data = self._load_rag_data(sona_path)
        self.graph = self._build_graph()
        
        # Initialize conversation logger
        self.logger = None
        if enable_logging:
            # Get persona name for logging
            persona_name = "default"
            if sona_path:
                try:
                    with open(sona_path, 'r') as f:
                        sona_data = json.load(f)
                        persona_name = sona_data.get("name", os.path.basename(sona_path).replace(".json", ""))
                except:
                    persona_name = os.path.basename(sona_path).replace(".json", "") if sona_path else "default"
            self.logger = ConversationLogger(persona_name=persona_name)
        
        # Initialize journal if configured
        self.journal = None
        if sona_path:
            # Initialize journal if configured in persona
            try:
                with open(sona_path, 'r') as f:
                    sona_data = json.load(f)
                    journal_path = sona_data.get("journal_path", "journal.json")
                    self.journal = Journal(journal_path=journal_path, memory=self.memory)
            except:
                # Default journal path
                self.journal = Journal(journal_path="journal.json", memory=self.memory)
        
        # Initialize external API manager (for weather, etc. - optional)
        self.external_apis = None
        if enable_external_apis:
            self.external_apis = ExternalAPIManager(db_path)
        
        # Initialize local services (calendar, reminders, tasks, finances)
        self.local_calendar = LocalCalendar(db_path)
        self.reminder_service = ReminderService(db_path)
        self.task_service = TaskService(db_path)
        self.financial_service = FinancialService(db_path)
        
        # Initialize MCP client
        self.mcp_client = None
        self.mcp_executor = None
        if enable_mcp:
            mcp_url = os.getenv("MCP_SERVER_URL")
            mcp_path = os.getenv("MCP_SERVER_PATH")
            
            # Try to read from config.json if not in environment
            if not mcp_url and not mcp_path:
                try:
                    config_path = "config.json"
                    if os.path.exists(config_path):
                        with open(config_path, "r") as f:
                            config = json.load(f)
                            mcp_url = config.get("mcp_server_url") or config.get("MCP_SERVER_URL")
                            mcp_path = config.get("mcp_server_path") or config.get("MCP_SERVER_PATH")
                except Exception:
                    pass
            
            # Try to connect to docker-mcp server (local only)
            if not mcp_url and not mcp_path:
                docker_url = DockerMCPServer.get_docker_mcp_url()
                if docker_url:
                    mcp_url = docker_url
            
            if mcp_url or mcp_path:
                print(f"DEBUG [MCP INIT]: Initializing MCP client with URL: {mcp_url}, Path: {mcp_path}")
                self.mcp_client = MCPClient(mcp_server_url=mcp_url, mcp_server_path=mcp_path)
                self.mcp_executor = MCPToolExecutor(self.mcp_client)
                # Test connection
                try:
                    tools = self.mcp_client.list_tools()
                    print(f"DEBUG [MCP INIT]: Successfully connected! Found {len(tools)} tools")
                except Exception as e:
                    print(f"DEBUG [MCP INIT]: Connection test failed: {e}")
            else:
                print("DEBUG [MCP INIT]: No MCP URL or path found. MCP disabled.")
        
    def _build_graph(self):
        """Build the LangGraph workflow"""
        if not LANGGRAPH_AVAILABLE:
            return None
        
        workflow = StateGraph(AgentState)
        
        # Define nodes
        workflow.add_node("analyze_input", self.analyze_input)
        workflow.add_node("retrieve_memories", self.retrieve_memories)
        workflow.add_node("get_personality_context", self.get_personality_context)
        workflow.add_node("generate_response", self.generate_response)
        workflow.add_node("store_memory", self.store_memory)
        workflow.add_node("adapt_personality", self.adapt_personality)
        workflow.add_node("check_proactivity", self.check_proactivity)
        
        # Define edges
        workflow.set_entry_point("analyze_input")
        
        workflow.add_edge("analyze_input", "retrieve_memories")
        workflow.add_edge("retrieve_memories", "get_personality_context")
        workflow.add_edge("get_personality_context", "generate_response")
        workflow.add_edge("generate_response", "store_memory")
        workflow.add_edge("store_memory", "adapt_personality")
        workflow.add_edge("adapt_personality", "check_proactivity")
        workflow.add_edge("check_proactivity", END)
        
        # Compile with memory for checkpointing
        memory_checkpointer = MemorySaver()
        return workflow.compile(checkpointer=memory_checkpointer)
    
    def analyze_input(self, state: AgentState) -> AgentState:
        """Analyze user input for sentiment, intent, and context"""
        user_input = state.get("user_input", "")
        
        # Simple sentiment analysis (can be enhanced with proper NLP)
        sentiment = self._estimate_sentiment(user_input)
        
        # Extract context (topics, entities, etc.)
        context = {
            "timestamp": datetime.now().isoformat(),
            "length": len(user_input),
            "has_question": "?" in user_input,
            "has_exclamation": "!" in user_input,
            "topics": self._extract_topics(user_input),
            "has_media": False,
            "media_files": []
        }
        
        # Check for media in interaction metadata
        interaction_metadata = state.get("interaction_metadata", {})
        if interaction_metadata.get("media_files"):
            context["has_media"] = True
            context["media_files"] = interaction_metadata["media_files"]
        
        state["user_sentiment"] = sentiment
        state["context"] = context
        
        return state
    
    def retrieve_memories(self, state: AgentState) -> AgentState:
        """Retrieve relevant memories based on current input"""
        user_input = state.get("user_input", "")
        context = state.get("context", {})
        topics = context.get("topics", [])
        
        # Get persona name for memory filtering (prevents cross-contamination)
        persona_name = "default"
        if self.sona_path:
            try:
                with open(self.sona_path, 'r') as f:
                    sona_data = json.load(f)
                    persona_name = sona_data.get("name", os.path.basename(self.sona_path).replace(".json", ""))
            except:
                persona_name = os.path.basename(self.sona_path).replace(".json", "") if self.sona_path else "default"
        
        # Prioritize topic-relevant memories first
        topic_memories = []
        if topics:
            # Get memories filtered by current topics (most relevant) AND persona
            topic_memories = self.memory.recall_episodic(
                limit=3,
                min_importance=0.3,  # Lower threshold for topic relevance
                tags=topics[:3],  # Filter by current topics
                days_back=30,
                persona=persona_name  # Filter by persona to prevent cross-contamination
            )
        
        # Get recent important memories (fallback if no topic matches)
        recent_memories = self.memory.recall_episodic(
            limit=2,  # Reduced from 5 to prioritize topic-relevant
            min_importance=0.5,
            days_back=7,  # Reduced from 30 days to focus on recent context
            persona=persona_name  # Filter by persona to prevent cross-contamination
        )
        
        # Combine and deduplicate (topic memories first, then recent)
        seen_ids = set()
        combined_memories = []
        for mem in topic_memories + recent_memories:
            if mem['id'] not in seen_ids:
                combined_memories.append(mem)
                seen_ids.add(mem['id'])
        
        # Limit to 5 total memories
        combined_memories = combined_memories[:5]
        
        # Get semantic memories related to topics
        semantic_memories = {}
        for topic in topics[:3]:  # Limit to top 3 topics
            semantic = self.memory.recall_semantic(key=topic)
            if semantic:
                semantic_memories[topic] = semantic
        
        # Only find related memories if we have topic-relevant memories
        related = []
        if topic_memories:
            related = self.memory.find_related_memories(
                topic_memories[0]["id"], 
                limit=2,  # Reduced from 3
                persona=persona_name  # Filter by persona to prevent cross-contamination
            )
        
        state["memories_retrieved"] = {
            "episodic": combined_memories,
            "semantic": semantic_memories,
            "related": related
        }
        
        return state
    
    def get_personality_context(self, state: AgentState) -> AgentState:
        """Get current personality context for response generation"""
        personality_context = self.personality.generate_personality_context()
        
        # Add relationship summary
        relationship_summary = self.memory.get_relationship_summary()
        personality_context += f"\n\nRELATIONSHIP HISTORY:\n{json.dumps(relationship_summary, indent=2)}"
        
        # Add quest system context for CJS persona
        if QUEST_SYSTEM_AVAILABLE and self.sona_path:
            sona_lower = self.sona_path.lower()
            if "cjs" in sona_lower or "carroll" in sona_lower:
                try:
                    quest_system = JimQuestSystem(cjs_json_path=self.sona_path)
                    active_quests = quest_system.get_active_quests()
                    quest_summary = quest_system.get_quest_summary()
                    
                    if active_quests:
                        personality_context += f"\n\nACTIVE QUESTS:\n"
                        for quest in active_quests[:3]:  # Limit to 3 most recent
                            personality_context += f"- {quest.get('title', 'Unknown Quest')}: {quest.get('progress_description', 'In progress')} ({quest.get('progress', 0)}%)\n"
                    
                    if quest_summary.get("completed_quests", 0) > 0:
                        personality_context += f"\nQUEST STATISTICS:\n"
                        personality_context += f"- Total quests completed: {quest_summary.get('completed_quests', 0)}\n"
                        personality_context += f"- Total gold earned: {quest_summary.get('total_gold_earned', 0)} gp\n"
                except Exception as e:
                    # Silently fail - quest system is optional
                    pass
        
        # Add conversation memory and learnings for Alex persona
        if self.sona_path:
            sona_lower = self.sona_path.lower()
            if "alex" in sona_lower:
                try:
                    with open(self.sona_path, 'r', encoding='utf-8') as f:
                        alex_data = json.load(f)
                    
                    # Add recent conversation logs
                    conversation_logs = alex_data.get("conversation_logs", [])
                    if conversation_logs:
                        recent_logs = conversation_logs[-3:]  # Last 3 conversations
                        personality_context += f"\n\nRECENT CONVERSATIONS:\n"
                        for log in recent_logs:
                            personality_context += f"- {log.get('date', 'Unknown')}: {log.get('summary', 'No summary')}\n"
                            if log.get('key_topics'):
                                personality_context += f"  Topics: {', '.join(log.get('key_topics', [])[:5])}\n"
                    
                    # Add learned information about Dallas
                    learned = alex_data.get("learned_about_dallas", {})
                    if learned:
                        personality_context += f"\n\nWHAT I KNOW ABOUT DALLAS:\n"
                        current_life = learned.get("current_life_situation", {})
                        if current_life.get("work"):
                            personality_context += f"Work: {', '.join(current_life['work'][:3])}\n"
                        if current_life.get("goals"):
                            personality_context += f"Goals: {', '.join(current_life['goals'][:3])}\n"
                        if current_life.get("challenges"):
                            personality_context += f"Current Challenges: {', '.join(current_life['challenges'][:3])}\n"
                        if learned.get("new_interests"):
                            personality_context += f"Interests: {', '.join(learned['new_interests'][:3])}\n"
                    
                    # Add conversation memory
                    memory = alex_data.get("conversation_memory", {})
                    if memory:
                        if memory.get("unresolved_topics"):
                            unresolved = [t.get("topic", "") for t in memory["unresolved_topics"][-3:] if t.get("status") == "pending"]
                            if unresolved:
                                personality_context += f"\nPENDING TOPICS TO FOLLOW UP:\n"
                                for topic in unresolved:
                                    personality_context += f"- {topic[:100]}\n"
                        
                        if memory.get("reminders_set"):
                            reminders = [r.get("reminder", "") for r in memory["reminders_set"][-3:]]
                            if reminders:
                                personality_context += f"\nACTIVE REMINDERS:\n"
                                for reminder in reminders:
                                    personality_context += f"- {reminder[:100]}\n"
                    
                    # Add relationship evolution
                    rel_evo = alex_data.get("relationship_evolution", {})
                    if rel_evo:
                        total_convos = rel_evo.get("total_conversations", 0)
                        comfort_level = rel_evo.get("comfort_level", "building")
                        personality_context += f"\nRELATIONSHIP STATUS:\n"
                        personality_context += f"- Total conversations: {total_convos}\n"
                        personality_context += f"- Comfort level: {comfort_level}\n"
                        if rel_evo.get("last_conversation_date"):
                            personality_context += f"- Last conversation: {rel_evo['last_conversation_date']}\n"
                except Exception as e:
                    # Silently fail - conversation memory is optional
                    pass
        
        state["personality_context"] = personality_context
        
        return state
    
    def generate_response(self, state: AgentState) -> AgentState:
        """Generate response using LLM with full context"""
        # Validate model_name at the very start - handle Model objects
        if not self.model_name:
            state["response"] = (
                f"Error: model_name is None or empty in agent instance. "
                f"Please check your config.json and ensure 'model_name' is set correctly, "
                f"or reinitialize the agent with a valid model name."
            )
            return state
        
        # If self.model_name is a Model object, extract the string
        if not isinstance(self.model_name, str):
            if hasattr(self.model_name, 'model'):
                model_attr = getattr(self.model_name, 'model')
                if model_attr and isinstance(model_attr, str):
                    self.model_name = model_attr.strip()
                else:
                    state["response"] = (
                        f"Error: Cannot extract model name string from Model object. "
                        f"Type: {type(self.model_name)}. "
                        f"Please check your config.json and ensure 'model_name' is set to a string."
                    )
                    return state
            else:
                state["response"] = (
                    f"Error: model_name is not a string and cannot extract model name. "
                    f"Type: {type(self.model_name)}. "
                    f"Please check your config.json and ensure 'model_name' is set to a string."
                )
                return state
        
        # Final check that it's a valid string
        if not self.model_name.strip():
            state["response"] = (
                f"Error: model_name is empty after extraction. "
                f"Please check your config.json and ensure 'model_name' is set correctly."
            )
            return state
        
        user_input = state.get("user_input", "")
        memories = state.get("memories_retrieved", {})
        personality_context = state.get("personality_context", "")
        user_sentiment = state.get("user_sentiment", 0.0)
        context = state.get("context", {})
        current_topics = context.get("topics", [])
        
        # Get current persona name for context labeling
        current_persona_name = "this persona"
        if self.sona_path:
            try:
                with open(self.sona_path, 'r') as f:
                    sona_data = json.load(f)
                    current_persona_name = sona_data.get("name", os.path.basename(self.sona_path).replace(".json", ""))
            except:
                current_persona_name = os.path.basename(self.sona_path).replace(".json", "") if self.sona_path else "this persona"
        
        # Check if persona has a system_prompt field (like Alex Mercer)
        # BUT: Skip it if using a Modelfile model (like jim-spohn) since the Modelfile already has the system prompt
        system_prompt = None
        use_modelfile = False
        
        # Detect if we're using a Modelfile model (models created from Modelfiles often have descriptive names)
        modelfile_indicators = ["jim-spohn", "custom", "modelfile"]
        if any(indicator in self.model_name.lower() for indicator in modelfile_indicators):
            use_modelfile = True
            # Don't load sona system_prompt - Modelfile already has it baked in
        else:
            # For non-Modelfile models, load sona system_prompt if available
            if hasattr(self.personality, 'base_personality') and isinstance(self.personality.base_personality, dict):
                system_prompt = self.personality.base_personality.get("system_prompt")
        
        # Build context for LLM
        context_parts = []
        
        # Use system_prompt if available (for personas like Alex Mercer) AND not using Modelfile
        if system_prompt and not use_modelfile:
            # STRONG ENFORCEMENT: Put system prompt FIRST and make it very clear
            context_parts.append("=" * 80)
            context_parts.append("SYSTEM INSTRUCTIONS - FOLLOW THESE EXACTLY:")
            context_parts.append("=" * 80)
            context_parts.append(system_prompt)
            context_parts.append("\n" + "=" * 80)
            context_parts.append("CRITICAL REMINDER: Use ONLY the information provided below. DO NOT make up, invent, or guess facts. If information is not provided, say 'I don't have that information' rather than guessing.")
            context_parts.append("DO NOT generate academic essays, random stories, or unrelated content. Stay focused on being a helpful personal assistant.")
            context_parts.append("\nMOST IMPORTANT: Always prioritize what the user JUST said in the 'CURRENT USER MESSAGE' section. If the user just told you something, use that information - do NOT rely on old memories if they conflict.")
            context_parts.append("\nFORMATTING REQUIREMENTS:")
            context_parts.append("- Use proper markdown formatting with clear structure")
            context_parts.append("- Use headings (##, ###) to organize sections when explaining multiple concepts")
            context_parts.append("- For lists, use '- ' for each item, each on its own line with proper spacing")
            context_parts.append("- Use double line breaks between paragraphs and sections")
            context_parts.append("- For code examples, use proper code blocks with language specification")
            context_parts.append("- Format examples clearly with proper indentation and spacing")
            context_parts.append("- Use bold (**text**) for emphasis on key terms or important points")
            context_parts.append("- Structure responses like: Brief intro → Clear explanation → Examples if needed → Summary")
            context_parts.append("\nExample of good formatting:")
            context_parts.append("## Section Title")
            context_parts.append("\nBrief introduction explaining the concept.\n")
            context_parts.append("- Point 1 with clear explanation")
            context_parts.append("- Point 2 with clear explanation")
            context_parts.append("\n```language")
            context_parts.append("code example here")
            context_parts.append("```\n")
            context_parts.append("**Key takeaway:** Summary point")
            context_parts.append("=" * 80)
            context_parts.append("\n\nCONTEXT FROM OUR RELATIONSHIP:")
        elif use_modelfile:
            # For Modelfile models, just add a note that RAG data provides additional context
            context_parts.append("ADDITIONAL CONTEXT AND MEMORIES (your Modelfile system prompt already contains your core identity):")
            context_parts.append("\n\nCRITICAL: Use ONLY the information provided below. DO NOT make up or invent facts. If information is not provided, say you don't have that information rather than guessing.")
            context_parts.append("\nMOST IMPORTANT: Always prioritize what the user JUST said in the 'CURRENT USER MESSAGE' section. If the user just told you something, use that information - do NOT rely on old memories if they conflict.")
        else:
            context_parts.append(personality_context)
            context_parts.append("\n\nCRITICAL: Use ONLY the information provided below. DO NOT make up or invent facts. If information is not provided, say you don't have that information rather than guessing.")
            context_parts.append("\nMOST IMPORTANT: Always prioritize what the user JUST said in the 'CURRENT USER MESSAGE' section. If the user just told you something, use that information - do NOT rely on old memories if they conflict.")
            context_parts.append("\nFORMATTING REQUIREMENTS:")
            context_parts.append("- Use proper markdown formatting with clear structure")
            context_parts.append("- Use headings (##, ###) to organize sections when explaining multiple concepts")
            context_parts.append("- For lists, use '- ' for each item, each on its own line with proper spacing")
            context_parts.append("- Use double line breaks between paragraphs and sections")
            context_parts.append("- For code examples, use proper code blocks with language specification")
            context_parts.append("- Format examples clearly with proper indentation and spacing")
            context_parts.append("- Use bold (**text**) for emphasis on key terms or important points")
            context_parts.append("- Structure responses like: Brief intro → Clear explanation → Examples if needed → Summary")
        
        # CRITICAL: Add CURRENT user input FIRST - this is what the user JUST said
        # This must be prioritized over everything else
        context_parts.append("\n" + "="*80)
        context_parts.append("CURRENT USER MESSAGE (MOST IMPORTANT - RESPOND TO THIS):")
        context_parts.append("="*80)
        context_parts.append(f"user: {user_input}")
        context_parts.append("="*80)
        context_parts.append("\nCRITICAL INSTRUCTIONS:")
        context_parts.append("- The message above is what the user JUST said. This is your PRIMARY focus.")
        context_parts.append("- Respond directly to what the user JUST said, not to old messages or memories.")
        context_parts.append("- If the user just told you something new, use that information immediately.")
        context_parts.append("- Old memories are for context only - do NOT use them if they conflict with what the user just said.")
        context_parts.append("- If the user corrects something or provides new information, that takes precedence over everything else.")
        context_parts.append("="*80 + "\n")
        
        # Add recent conversation history for context (but current message is already above)
        if state.get("messages"):
            context_parts.append("\nRECENT CONVERSATION HISTORY (for context only - current message is above):")
            # Show last 4 messages (excluding current which is already shown)
            for msg in state["messages"][-4:]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                context_parts.append(f"{role}: {content}")
        
        # Add explicit instruction to stay on current topic
        if current_topics:
            context_parts.append(f"\nCRITICAL: Stay focused on the current topic: {', '.join(current_topics[:3])}. Do NOT bring up unrelated topics from old memories unless directly relevant to what Dallas JUST asked NOW.")
        
        # Add episodic memories (only topic-relevant ones)
        # IMPORTANT: These are PERSONA-SPECIFIC conversations - only conversations YOU had with the user
        # These are NOT shared with other personas
        if memories.get("episodic"):
            context_parts.append(f"\nYOUR PREVIOUS CONVERSATIONS WITH {current_persona_name.upper()} (PERSONA-SPECIFIC MEMORIES):")
            context_parts.append("CRITICAL: These are conversations YOU had with the user. Other personas (like Alex Mercer, Izzy-Chan, Jimmy Spohn) have their OWN separate conversations.")
            context_parts.append("DO NOT confuse these with information from journal or RAG data - those are shared knowledge, not personal conversations.")
            for mem in memories["episodic"][:3]:
                context_parts.append(f"- [{mem['timestamp']}] {mem['content'][:200]}...")
            context_parts.append("NOTE: If these memories conflict with what the user just said, use what the user just said.")
        
        # Add semantic memories
        if memories.get("semantic"):
            context_parts.append("\nRELEVANT KNOWLEDGE:")
            for key, value in memories["semantic"].items():
                if isinstance(value, dict):
                    context_parts.append(f"- {key}: {value.get('value', '')}")
        
        # Track RAG usage for logging
        rag_files_used = []
        if self.rag_data:
            if isinstance(self.rag_data, dict) and "_loaded_files" in self.rag_data:
                rag_files_used = self.rag_data.get("_loaded_files", [])
            elif isinstance(self.rag_data, dict) and "_rag_data" in self.rag_data:
                rag_files_used = list(self.rag_data.get("_rag_data", {}).keys())
            else:
                # Single RAG file - try to get filename from sona
                if self.sona_path:
                    try:
                        with open(self.sona_path, 'r') as f:
                            sona_data = json.load(f)
                            rag_file = sona_data.get("rag_file", "unknown")
                            rag_files_used = [rag_file]
                    except:
                        rag_files_used = ["unknown"]
        
        # Add RAG data context if available
        # For Modelfile models, use RAG more selectively to avoid conflicts
        if self.rag_data:
            # Handle both single RAG file and multiple loaded files
            rag_data_to_use = self.rag_data
            if isinstance(self.rag_data, dict) and "_rag_data" in self.rag_data:
                # Multiple RAG files loaded - use the combined data
                rag_data_to_use = self.rag_data
            
            # Check if user query matches RAG content (simple keyword matching)
            user_input_lower = user_input.lower()
            rag_str = json.dumps(rag_data_to_use, indent=2).lower()
            
            # For Modelfile models, be more selective with RAG data to avoid conflicts
            if use_modelfile:
                # Always include RAG data for Modelfile models, but prioritize relevant sections
                user_words = set(user_input_lower.split())
                # Add important keywords that should always trigger RAG inclusion
                important_keywords = ["adventure", "guild", "story", "quest", "rank", "isekai", "aetheria", "millbrook", "dungeon", "monster", "magic", "crystal"]
                user_words.update([kw for kw in important_keywords if kw in user_input_lower])
                
                relevant_sections = []
                rag_lines = json.dumps(rag_data_to_use, indent=2).split('\n')
                
                # Look for relevant sections
                for line in rag_lines:
                    line_lower = line.lower()
                    if any(word in line_lower for word in user_words if len(word) > 3):
                        relevant_sections.append(line)
                        if len('\n'.join(relevant_sections)) > 2000:  # Smaller limit for Modelfile
                            break
                
                # If we have relevant sections OR if query mentions important keywords, include RAG
                if relevant_sections or any(kw in user_input_lower for kw in important_keywords):
                    if relevant_sections:
                        context_parts.append(f"\nKNOWLEDGE FROM RAG DATA (SHARED KNOWLEDGE - NOT PERSONAL CONVERSATIONS):")
                        context_parts.append("CRITICAL: This is general knowledge/data, NOT conversations you had with the user.")
                        context_parts.append("This information is shared across personas - it's not persona-specific conversation memory.")
                        context_parts.append(f"{chr(10).join(relevant_sections[:30])}")
                    else:
                        # Include key sections even if no direct match (for adventure/guild queries)
                        rag_str = json.dumps(rag_data_to_use, indent=2)
                        # Extract key sections about adventures, guild, status
                        key_sections = []
                        for section_name in ["recent_adventures", "jim_current_status", "adventurer_rank", "guild_branch", "jim_skills_and_abilities"]:
                            if section_name in rag_str.lower():
                                # Find and include that section
                                lines = rag_str.split('\n')
                                in_section = False
                                for i, line in enumerate(lines):
                                    if section_name.replace('_', ' ') in line.lower() or section_name in line.lower():
                                        in_section = True
                                    if in_section:
                                        key_sections.append(line)
                                        if len('\n'.join(key_sections)) > 1500:
                                            break
                                    if in_section and line.strip().startswith('}') and line.count('}') > line.count('{'):
                                        break
                        if key_sections:
                            context_parts.append(f"\nYOUR CURRENT ISEKAI LIFE (from your adventure log - SHARED KNOWLEDGE):")
                            context_parts.append("CRITICAL: This is general knowledge/data, NOT conversations you had with the user.")
                            context_parts.append(f"{chr(10).join(key_sections[:40])}")
                # Don't add RAG if no relevant matches - let Modelfile handle it
            else:
                # For non-Modelfile models, use full RAG as before
                if len(rag_str) > 5000:
                    # Extract keywords from user input
                    user_words = set(user_input_lower.split())
                    # Find relevant sections (simplified - could be improved)
                    relevant_sections = []
                    rag_lines = json.dumps(rag_data_to_use, indent=2).split('\n')
                    for line in rag_lines:
                        line_lower = line.lower()
                        if any(word in line_lower for word in user_words if len(word) > 3):
                            relevant_sections.append(line)
                            if len('\n'.join(relevant_sections)) > 3000:
                                break
                    
                    if relevant_sections:
                        context_parts.append(f"\nKNOWLEDGE FROM RAG DATA (SHARED KNOWLEDGE - NOT PERSONAL CONVERSATIONS):")
                        context_parts.append("CRITICAL: This is general knowledge/data, NOT conversations you had with the user.")
                        context_parts.append("This information is shared across personas - it's not persona-specific conversation memory.")
                        context_parts.append(f"{chr(10).join(relevant_sections[:50])}")
                    else:
                        # Fall back to full RAG if no matches
                        context_parts.append(f"\nKNOWLEDGE FROM RAG DATA (SHARED KNOWLEDGE - NOT PERSONAL CONVERSATIONS):")
                        context_parts.append("CRITICAL: This is general knowledge/data, NOT conversations you had with the user.")
                        context_parts.append(f"{json.dumps(rag_data_to_use, indent=2)[:5000]}...")
                else:
                    context_parts.append(f"\nKNOWLEDGE FROM RAG DATA (SHARED KNOWLEDGE - NOT PERSONAL CONVERSATIONS):")
                    context_parts.append("CRITICAL: This is general knowledge/data, NOT conversations you had with the user.")
                    context_parts.append(f"{json.dumps(rag_data_to_use, indent=2)}")
        
        # Track journal usage for logging
        journal_entries_used = []
        
        # Add journal context if available
        if self.journal:
            # Check if user is asking about history/past events
            history_keywords = ["history", "past", "remember", "before", "ago", "used to", 
                              "from my", "my history", "tell me about", "something about"]
            user_input_lower = user_input.lower()
            
            # Check if this is a calendar/upcoming events query - SKIP journal for these
            calendar_keywords = ["calendar", "calendars", "upcoming", "events", "schedule", "scheduled", 
                               "what's on", "what is on", "show me my calendar", "my calendar",
                               "appointments", "meetings", "when is", "when are"]
            is_calendar_query = any(keyword in user_input_lower for keyword in calendar_keywords)
            
            is_history_query = any(keyword in user_input_lower for keyword in history_keywords)
            
                # Skip journal for calendar queries - calendar events are separate from historical events
            if is_calendar_query:
                # Don't add journal for calendar queries - they're asking about upcoming events, not history
                pass
            
            if is_history_query:
                # Search journal for relevant entries
                journal_search_results = self.journal.search(user_input)
                if journal_search_results:
                    # Track which entries were used
                    for result in journal_search_results[:5]:
                        result_type = result.get("type", "unknown")
                        result_data = result.get("data", {})
                        if result_type == "timeline":
                            year = result_data.get('year', 'Unknown')
                            journal_entries_used.append(f"Timeline[{year}]: {result_data.get('content', '')[:50]}...")
                        elif result_type == "friend":
                            journal_entries_used.append(f"Friend: {result_data.get('name', '')}")
                        elif result_type == "location":
                            journal_entries_used.append(f"Location: {result_data.get('city', '')}")
                    journal_context = "\n=== JOURNAL SEARCH RESULTS (SHARED HISTORICAL DATA) ===\n"
                    journal_context += "CRITICAL: This is HISTORICAL biographical information, NOT conversations you had with the user.\n"
                    journal_context += "This information is shared - other personas can also see it. It's NOT persona-specific conversation memory.\n"
                    journal_context += "DO NOT confuse this with your own conversations with the user.\n\n"
                    for result in journal_search_results[:5]:  # Limit to 5 results
                        result_type = result.get("type", "unknown")
                        result_data = result.get("data", {})
                        if result_type == "timeline":
                            year_str = f"[{result_data.get('year', 'Unknown')}]" if result_data.get('year') else "[Unknown Year]"
                            journal_context += f"  Timeline Entry {year_str}: {result_data.get('content', '')[:300]}\n"
                        elif result_type == "friend":
                            memories = result_data.get('memories', [])
                            mem_str = ', '.join(memories[:2]) if memories else "No specific memories"
                            journal_context += f"  Friend: {result_data.get('name', '')} - {mem_str}\n"
                        elif result_type == "location":
                            journal_context += f"  Location: {result_data.get('city', '')}, {result_data.get('state', '')}\n"
                    journal_context += "\n=== END JOURNAL ===\n"
                    context_parts.append(journal_context)
                else:
                    # Fall back to summary if no search results
                    journal_summary = self.journal.get_summary()
                    if journal_summary and len(journal_summary.strip()) > 50:
                        if self.sona_path and ("cjs" in self.sona_path.lower() or "carroll" in self.sona_path.lower()):
                            context_parts.append(f"\n=== JOURNAL (SHARED HISTORICAL DATA) ===\nCRITICAL: This is HISTORICAL biographical information, NOT conversations you had with the user.\nThis information is shared - other personas can also see it. It's NOT persona-specific conversation memory.\n{journal_summary}\n=== END JOURNAL ===\n")
                        else:
                            context_parts.append(f"\n=== JOURNAL (SHARED HISTORICAL DATA) ===\nCRITICAL: This is HISTORICAL biographical information, NOT conversations you had with the user.\nThis information is shared - other personas can also see it. It's NOT persona-specific conversation memory.\nContains many references to you and shared memories.\n{journal_summary}\n=== END JOURNAL ===\n")
                    else:
                        context_parts.append("\n=== JOURNAL ===\nThe journal exists but contains minimal information. If asked about history, say you don't have that specific information yet.\n=== END JOURNAL ===\n")
            else:
                # Use summary for non-history queries (but skip for calendar queries)
                if not is_calendar_query:
                    journal_summary = self.journal.get_summary()
                    if journal_summary and len(journal_summary.strip()) > 50:
                        # Add special note for CJS persona about Jim references
                        if self.sona_path and ("cjs" in self.sona_path.lower() or "carroll" in self.sona_path.lower()):
                            context_parts.append(f"\n=== JOURNAL (HISTORICAL EVENTS - NOT CURRENT CALENDAR) ===\nCRITICAL: This is HISTORICAL biographical information, NOT current calendar events or scheduled appointments.\nUse ONLY this information.\n{journal_summary}\n=== END JOURNAL ===\n")
                        else:
                            context_parts.append(f"\n=== JOURNAL (HISTORICAL EVENTS - NOT CURRENT CALENDAR) ===\nCRITICAL: This is HISTORICAL biographical information, NOT current calendar events or scheduled appointments.\nUse ONLY this information. Contains many references to you and shared memories.\n{journal_summary}\n=== END JOURNAL ===\n")
                    else:
                        # Journal exists but is empty/minimal
                        context_parts.append("\n=== JOURNAL ===\nThe journal exists but contains minimal information.\n=== END JOURNAL ===\n")
        
        # Add local services context (calendar, reminders, tasks)
        # Check if this is a calendar query to prioritize calendar context
        user_input_lower = user_input.lower()
        calendar_keywords = ["calendar", "calendars", "upcoming", "events", "schedule", "scheduled", 
                           "what's on", "what is on", "show me my calendar", "my calendar",
                           "appointments", "meetings", "when is", "when are"]
        is_calendar_query = any(keyword in user_input_lower for keyword in calendar_keywords)
        
        local_context, local_services_data = self._get_local_services_context(user_input)
        
        # Track local services data sources for logging (always set, even if empty)
        local_services = local_services_data
        
        if local_context:
            if is_calendar_query:
                # For calendar queries, prioritize and clearly label calendar events
                context_parts.append(f"\n{'='*80}")
                context_parts.append("UPCOMING CALENDAR EVENTS (CURRENT SCHEDULE - NOT HISTORICAL):")
                context_parts.append(f"{'='*80}")
                context_parts.append("CRITICAL: These are ACTUAL calendar events with specific dates/times.")
                context_parts.append("These are NOT historical events from the journal.")
                context_parts.append("Use ONLY these calendar events when answering calendar questions.")
                context_parts.append("DO NOT confuse journal timeline entries (which are historical) with calendar events.")
                context_parts.append(f"{'='*80}\n")
            context_parts.append(f"\nLOCAL SERVICES CONTEXT:\n{local_context}")
        
        # Check for calendar actions (LOCAL)
        calendar_action = self.handle_calendar_actions(user_input)
        if calendar_action:
            context_parts.append(calendar_action)
        
        # Check for reminder actions (LOCAL)
        reminder_action = self.handle_reminder_actions(user_input)
        if reminder_action:
            context_parts.append(reminder_action)
        
        # Check for task actions (LOCAL)
        task_action = self.handle_task_actions(user_input)
        if task_action:
            context_parts.append(task_action)
        
        # Check for financial actions (LOCAL)
        financial_action = self.handle_financial_actions(user_input)
        if financial_action:
            context_parts.append(financial_action)
        
        # Add external API context (weather, etc. - optional)
        if self.external_apis:
            api_context = self._get_external_api_context(user_input)
            if api_context:
                context_parts.append(f"\nEXTERNAL CONTEXT:\n{api_context}")
        
        # Track MCP tool usage for logging (initialize early so it's available everywhere)
        mcp_tools_used = []
        
        # Add MCP tools context
        web_search_results = None
        if self.mcp_executor:
            try:
                tools_summary = self.mcp_executor.get_available_tools_summary()
            except Exception as e:
                print(f"DEBUG [MCP TOOLS]: Error getting tools summary: {e}")
                tools_summary = "MCP tools available but connection issue"
            if tools_summary:
                context_parts.append(f"\n{tools_summary}")
                context_parts.append("\nIMPORTANT: If the user asks for current information, news, or anything that requires up-to-date web data, use the 'web_search' tool automatically.")
                context_parts.append("\nWEB SEARCH USAGE:")
                context_parts.append("- For general searches: Use the query as-is (e.g., 'latest world news')")
                context_parts.append("- For site-specific searches: Use 'site:domain.com' syntax (e.g., 'site:spohnz.com' or 'site:spohnz.com search term')")
                context_parts.append("- When user mentions a website domain (.com, .org, etc.), use web_search with 'site:' prefix")
                context_parts.append("- Example: User says 'search spohnz.com' → Use web_search with query 'site:spohnz.com'")
                context_parts.append("- The tool will be called automatically when you detect search-related queries.")
                context_parts.append("\nIMAGE GENERATION:")
                context_parts.append("- If an image was generated (you'll see 'IMAGE GENERATED SUCCESSFULLY' above), simply acknowledge it naturally.")
                context_parts.append("- DO NOT explain how tools work - if an image was requested, it's already been generated.")
                context_parts.append("- Just say something like: 'Done! I've created that image for you' or 'Here's your image!'")
            
            # Auto-detect and execute web search if needed
            search_keywords = [
                "search the web", "search for", "look up", "find information about", 
                "latest news about", "recent news", "what's happening with", 
                "current events", "web search", "search online", "google",
                "what's the latest", "tell me about", "find out about",
                "get information", "what happened with", "news about",
                "what is", "who is", "where is", "when is", "how is",
                "tell me something about", "what do you know about",
                ".com", ".org", ".net", ".io", "website", "site:"
            ]
            user_input_lower = user_input.lower()
            
            # Track MCP tool usage for logging (initialize early so it's available everywhere)
            mcp_tools_used = []
            
            # Check if user wants web search
            needs_search = any(keyword in user_input_lower for keyword in search_keywords)
            
            # Also check for question patterns that suggest current information is needed
            question_patterns = ["latest", "recent", "current", "now", "today", "2025"]
            is_current_info_query = any(pattern in user_input_lower for pattern in question_patterns)
            
            # Check for domain names or URLs (likely web search needed)
            has_domain = any(ext in user_input_lower for ext in [".com", ".org", ".net", ".io", ".edu", ".gov"])
            if has_domain:
                needs_search = True
            
            print(f"DEBUG [WEB SEARCH]: needs_search={needs_search}, has_domain={has_domain}, mcp_executor={self.mcp_executor is not None}")
            
            # Check if weather query but weather API not available - use web search as fallback
            weather_keywords = ["weather", "temperature", "forecast", "rain", "snow", 
                               "sunny", "cloudy", "hot", "cold", "tomorrow", "morning"]
            is_weather_query = any(keyword in user_input_lower for keyword in weather_keywords)
            
            # If weather query and weather API not configured, use web search
            if is_weather_query and self.external_apis:
                weather_api_configured = "weather" in self.external_apis.api_configs and self.external_apis.api_configs["weather"].get('enabled', False)
                if not weather_api_configured:
                    needs_search = True
                    search_query = user_input  # Use full query for weather searches
            
            if needs_search or is_current_info_query or has_domain:
                # Extract search query
                search_query = user_input
                # Try to extract a cleaner query
                for keyword in search_keywords:
                    if keyword in user_input_lower:
                        # Extract text after the keyword
                        parts = user_input_lower.split(keyword, 1)
                        if len(parts) > 1:
                            search_query = parts[1].strip()
                            # Remove common trailing phrases but preserve domains
                            if "." not in search_query.split("?")[0].split(".")[0]:
                                search_query = search_query.split("?")[0].split(".")[0].strip()
                            else:
                                # Preserve domain names
                                search_query = search_query.split("?")[0].strip()
                            break
                
                # If no keyword found but it's a current info query or has domain, use the whole query
                if search_query == user_input and (is_current_info_query or has_domain):
                    # Remove question words and clean up, but preserve domain names
                    search_query = user_input
                    for word in ["can you", "please", "tell me something", "tell me", "what", "is", "are", "the"]:
                        if word in search_query.lower():
                            # Only remove if it's not part of a domain
                            search_query_lower = search_query.lower()
                            word_pos = search_query_lower.find(word)
                            if word_pos >= 0:
                                # Check if word is part of a domain (has . before or after)
                                before = search_query_lower[max(0, word_pos-5):word_pos]
                                after = search_query_lower[word_pos+len(word):word_pos+len(word)+5]
                                if "." not in before and "." not in after:
                                    search_query = search_query[:word_pos] + search_query[word_pos+len(word):].strip()
                                    break
                
                # If still the full input and has domain, extract domain or key phrase
                if search_query == user_input and has_domain:
                    # Try to extract domain name
                    domain_match = re.search(r'\b[\w-]+\.(?:com|org|net|io|edu|gov|co|uk|us)\b', user_input, re.IGNORECASE)
                    if domain_match:
                        domain = domain_match.group(0)
                        # Check if user wants to search within the site
                        # If they mention "search [domain]" or "[domain] site", use site: syntax
                        # Also check if domain appears at end of query (likely site-specific search)
                        is_site_search = (
                            "search" in user_input_lower and domain.lower() in user_input_lower or
                            "site" in user_input_lower or
                            user_input_lower.strip().endswith(domain.lower()) or
                            user_input_lower.strip().endswith(domain.lower() + ".")
                        )
                        
                        if is_site_search:
                            # Extract any additional search terms after the domain
                            remaining_text = user_input_lower.replace(domain.lower(), "").replace("search", "").replace("site", "").replace("the", "").strip()
                            # Remove common words
                            remaining_words = [w for w in remaining_text.split() if w.lower() not in ["the", "on", "in", "at", "to", "for", "of", "a", "an", "use", "tool"]]
                            if remaining_words:
                                search_query = f"site:{domain} {' '.join(remaining_words[:3])}"
                            else:
                                search_query = f"site:{domain}"
                        else:
                            # Just use the domain as-is (might be general search)
                            search_query = domain
                    else:
                        # Extract key phrase (remove common words)
                        words = user_input.split()
                        # Keep words that look like they're the subject (not common question words)
                        key_words = [w for w in words if w.lower() not in ["tell", "me", "something", "about", "what", "is", "are", "the", "a", "an"]]
                        search_query = " ".join(key_words[:5])  # Limit to 5 words
                
                if search_query and len(search_query) > 3:
                    # Ensure site: prefix is added if domain detected and user wants site search
                    if has_domain and "site:" not in search_query.lower():
                        domain_match = re.search(r'\b[\w-]+\.(?:com|org|net|io|edu|gov|co|uk|us)\b', search_query, re.IGNORECASE)
                        if domain_match and ("search" in user_input_lower or user_input_lower.strip().endswith(domain_match.group(0).lower())):
                            domain = domain_match.group(0)
                            # Remove domain from query and add site: prefix
                            query_without_domain = search_query.replace(domain, "").strip()
                            if query_without_domain:
                                search_query = f"site:{domain} {query_without_domain}"
                            else:
                                search_query = f"site:{domain}"
                    
                    # mcp_tools_used already initialized above
                    try:
                        # Call web search tool
                        print(f"DEBUG [WEB SEARCH]: Calling web_search with query: {search_query}")
                        search_result = self.mcp_executor.execute_tool(
                            "web_search",
                            {"query": search_query, "max_results": 5},
                            context={"user_query": user_input}
                        )
                        
                        print(f"DEBUG [WEB SEARCH RESULT]: success={search_result.get('success') if search_result else False}, has_output={bool(search_result and search_result.get('output'))}")
                        print(f"DEBUG [WEB SEARCH RESULT DETAIL]: {search_result}")
                        
                        if search_result and search_result.get("success"):
                            web_search_output = search_result.get("output")
                            # Handle both string and dict outputs
                            if isinstance(web_search_output, dict):
                                # Extract text from dict if needed
                                web_search_output = web_search_output.get("text", str(web_search_output))
                            
                            if web_search_output:
                                web_search_results = str(web_search_output)
                                context_parts.append(f"\n\nWEB SEARCH RESULTS (use this information to answer the user's question - cite sources when relevant):\n{web_search_results}")
                                mcp_tools_used.append(f"web_search: {search_query}")
                                print(f"DEBUG [WEB SEARCH]: Successfully added search results to context ({len(web_search_results)} chars)")
                            else:
                                print(f"DEBUG [WEB SEARCH]: Search succeeded but output is empty. Result: {search_result}")
                        else:
                            print(f"DEBUG [WEB SEARCH]: Search failed or returned no results. Result: {search_result}")
                    except Exception as e:
                        # If tool call fails, continue without search results
                        print(f"DEBUG [WEB SEARCH ERROR]: {e}")
                        import traceback
                        traceback.print_exc()
            
            # Auto-detect Red Hat style guide questions and load relevant guides
            style_guide_keywords = [
                "style guide", "styleguide", "style-guide",
                "callout", "callouts", "admonition", "admonitions",
                "asciidoc", "ascii doc", "ascii-doc",
                "formatting", "format", "syntax",
                "lecture", "ge", "guided exercise", "dynolab", "lab",
                "red hat content", "redhat content", "training content",
                "how do i", "how to", "how can i", "what is the", "what are the",
                "code block", "code blocks", "source code", "listing"
            ]
            
            needs_style_guide = any(keyword in user_input_lower for keyword in style_guide_keywords)
            
            # Load Red Hat style guides if question is about content standards
            if needs_style_guide:
                style_guides_context = self._load_redhat_style_guides()
                if style_guides_context:
                    context_parts.append("\n" + "="*80)
                    context_parts.append("RED HAT CONTENT STANDARDS & STYLE GUIDES:")
                    context_parts.append("="*80)
                    context_parts.append(style_guides_context)
                    context_parts.append("="*80 + "\n")
                    print(f"DEBUG [STYLE GUIDES]: Loaded Red Hat style guides for question about: {user_input[:100]}")
            
            # Auto-detect and execute Red Hat content creation/update if needed
            redhat_content_keywords = [
                "create a lecture", "create lecture", "make a lecture", "generate lecture",
                "create a ge", "create ge", "create guided exercise", "make a ge",
                "create lab", "create lab script", "create dynolab", "create dynolabs",
                "red hat content", "redhat content", "training content",
                "create lecture and ge", "create lecture and lab", "create ge and lab",
                "lecture on", "ge on", "lab on", "guided exercise on",
                "review.*lecture", "update.*lecture", "review.*ge", "update.*ge",
                "review.*lab", "update.*lab", "fix.*lecture", "fix.*ge"
            ]
            
            # Check for Red Hat content keywords using regex patterns
            needs_redhat_content = False
            for keyword in redhat_content_keywords:
                if re.search(keyword, user_input_lower):
                    needs_redhat_content = True
                    break
            
            # Check if this is a review/update request (has file path)
            is_review_update = any(keyword in user_input_lower for keyword in ["review", "update", "fix"]) and any(keyword in user_input_lower for keyword in ["lecture", "ge", "lab", ".adoc"])
            
            print(f"DEBUG [DETECTION]: is_review_update={is_review_update}, mcp_executor={self.mcp_executor is not None}")
            
            # Handle review/update requests
            if is_review_update and self.mcp_executor:
                print(f"DEBUG [REDHAT CONTENT]: Red Hat content review/update detected!")
                try:
                    # Extract file path from user input
                    file_path = None
                    path_patterns = [
                        r"(?:at|in|file|path)[:\s]+([^\s]+\.adoc)",
                        r"([^\s]+\.adoc)",
                        r"(\.\.?/[\w/]+\.adoc)",
                        r"(/[\w/]+\.adoc)"
                    ]
                    for pattern in path_patterns:
                        match = re.search(pattern, user_input, re.IGNORECASE)
                        if match:
                            file_path = match.group(1).strip()
                            # Resolve relative paths
                            if file_path.startswith("../") or file_path.startswith("./"):
                                # If path starts with ../dev, resolve from home directory
                                if file_path.startswith("../dev"):
                                    # Resolve relative to home directory
                                    home_dir = os.path.expanduser("~")
                                    # Remove ../ and join with home directory
                                    file_path = file_path.replace("../dev", "dev", 1)
                                    file_path = os.path.join(home_dir, file_path)
                                    file_path = os.path.abspath(file_path)
                                else:
                                    # Resolve relative to current working directory
                                    file_path = os.path.abspath(file_path)
                            elif not os.path.isabs(file_path):
                                # Relative path without ../
                                file_path = os.path.abspath(file_path)
                            
                            # Normalize the path
                            file_path = os.path.normpath(file_path)
                            break
                    
                    print(f"DEBUG [FILE PATH]: Extracted path: {file_path}, exists: {os.path.exists(file_path) if file_path else False}")
                    
                    if file_path:
                        # Read the file using MCP file_reader tool if available
                        try:
                            print(f"DEBUG [MCP TOOL]: Calling file_reader with filename: {file_path}")
                            file_result = self.mcp_executor.execute_tool(
                                "file_reader",
                                {"filename": file_path},  # Use "filename" not "file_path"
                                context={"user_query": user_input}
                            )
                            
                            print(f"DEBUG [MCP RESULT]: {file_result}")
                            
                            if file_result and file_result.get("success") and not file_result.get("isError"):
                                # Extract content from result - handle multiple possible formats
                                output = file_result.get("output", {})
                                content_text = None
                                
                                # Format 1: Direct text string
                                if isinstance(output, str):
                                    content_text = output
                                # Format 2: Dict with content field
                                elif isinstance(output, dict):
                                    # Check for MCP format: {"content": [{"type": "text", "text": ...}]}
                                    if "content" in output:
                                        content_list = output["content"]
                                        if isinstance(content_list, list) and len(content_list) > 0:
                                            content_item = content_list[0]
                                            if isinstance(content_item, dict):
                                                # Extract text field
                                                content_text = content_item.get("text", str(content_item))
                                            else:
                                                content_text = str(content_item)
                                        else:
                                            content_text = str(content_list)
                                    # Check for direct text field
                                    elif "text" in output:
                                        content_text = output["text"]
                                    # Check if output itself is the content (nested structure)
                                    elif isinstance(output, dict) and len(output) == 1 and "text" in list(output.values())[0]:
                                        content_text = list(output.values())[0]["text"]
                                    else:
                                        # Try to find any text-like field
                                        for key in ["text", "content", "data", "file_content"]:
                                            if key in output:
                                                val = output[key]
                                                if isinstance(val, str):
                                                    content_text = val
                                                    break
                                                elif isinstance(val, list) and len(val) > 0:
                                                    if isinstance(val[0], dict) and "text" in val[0]:
                                                        content_text = val[0]["text"]
                                                        break
                                    # Last resort: convert to string
                                    if not content_text:
                                        content_text = str(output)
                                else:
                                    content_text = str(output)
                                
                                if not content_text:
                                    raise ValueError("Could not extract content from file_reader result")
                                
                                # Load style guides
                                style_guides_context = self._load_redhat_style_guides()
                                
                                # Add file content and style guides to context for review
                                context_parts.append("\n" + "="*80)
                                context_parts.append("FILE TO REVIEW AND UPDATE:")
                                context_parts.append("="*80)
                                context_parts.append(f"File Path: {file_path}\n")
                                context_parts.append("File Content:")
                                context_parts.append("-" * 80)
                                context_parts.append(content_text)
                                context_parts.append("-" * 80)
                                
                                if style_guides_context:
                                    context_parts.append("\n" + "="*80)
                                    context_parts.append("RED HAT CONTENT STANDARDS & STYLE GUIDES:")
                                    context_parts.append("="*80)
                                    context_parts.append(style_guides_context)
                                    context_parts.append("="*80)
                                
                                # Load instruction files for more context
                                instructions_context = self._load_redhat_instructions()
                                if instructions_context:
                                    context_parts.append("\n" + "="*80)
                                    context_parts.append("RED HAT CONTENT INSTRUCTIONS:")
                                    context_parts.append("="*80)
                                    context_parts.append(instructions_context)
                                    context_parts.append("="*80)
                                
                                context_parts.append("\n" + "="*80)
                                context_parts.append("INSTRUCTIONS:")
                                context_parts.append("="*80)
                                context_parts.append("Review the file content above against the Red Hat style guides and standards.")
                                context_parts.append("Identify ALL formatting issues, structural problems, and style violations.")
                                context_parts.append("Provide the COMPLETE updated file content that follows ALL Red Hat formatting rules.")
                                context_parts.append("Include proper AsciiDoc formatting, callouts where appropriate, correct heading structure,")
                                context_parts.append("proper code block formatting, and adherence to all style guide requirements.")
                                context_parts.append("Output the complete corrected file content ready to save.")
                                context_parts.append("="*80 + "\n")
                                
                                mcp_tools_used.append(f"file_reader: {file_path}")
                                print(f"DEBUG [SUCCESS]: File read successfully, {len(content_text)} characters loaded")
                            else:
                                error_msg = file_result.get("error", "Unknown error") if file_result else "No result returned"
                                print(f"DEBUG [ERROR]: File reading failed: {error_msg}")
                                context_parts.append(f"\n\nNOTE: Could not read file {file_path}. Error: {error_msg}")
                                # Try direct file read as fallback
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        content_text = f.read()
                                    style_guides_context = self._load_redhat_style_guides()
                                    if style_guides_context:
                                        context_parts.append("\n" + "="*80)
                                        context_parts.append("FILE CONTENT (read directly):")
                                        context_parts.append("="*80)
                                        context_parts.append(content_text)
                                        context_parts.append("\n" + "="*80)
                                        context_parts.append("RED HAT STYLE GUIDES:")
                                        context_parts.append("="*80)
                                        context_parts.append(style_guides_context)
                                        context_parts.append("="*80 + "\n")
                                        print(f"DEBUG [FALLBACK]: Read file directly, {len(content_text)} characters")
                                except Exception as fallback_error:
                                    print(f"DEBUG [FALLBACK ERROR]: {fallback_error}")
                                    context_parts.append(f"\n\nNOTE: Direct file read also failed: {fallback_error}")
                        except Exception as e:
                            print(f"DEBUG [EXCEPTION]: File reading exception: {e}")
                            import traceback
                            traceback.print_exc()
                            # Try direct file read as fallback
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content_text = f.read()
                                style_guides_context = self._load_redhat_style_guides()
                                if style_guides_context:
                                    context_parts.append("\n" + "="*80)
                                    context_parts.append("FILE CONTENT (read directly after MCP failure):")
                                    context_parts.append("="*80)
                                    context_parts.append(content_text)
                                    context_parts.append("\n" + "="*80)
                                    context_parts.append("RED HAT STYLE GUIDES:")
                                    context_parts.append("="*80)
                                    context_parts.append(style_guides_context)
                                    context_parts.append("="*80 + "\n")
                            except Exception as fallback_error:
                                context_parts.append(f"\n\nNOTE: Could not read file {file_path}. MCP error: {e}, Direct read error: {fallback_error}")
                    else:
                        print(f"DEBUG [NO PATH]: Could not extract file path from: {user_input}")
                        context_parts.append(f"\n\nNOTE: File path not found or could not be extracted from request. Please provide the full path to the file.")
                except Exception as e:
                    print(f"DEBUG [REVIEW ERROR]: Review/update detection error: {e}")
                    import traceback
                    traceback.print_exc()
            
            if needs_redhat_content and self.mcp_executor and not is_review_update:
                print(f"DEBUG [REDHAT CONTENT]: Red Hat content creation detected!")
                try:
                    # Extract output directory if specified
                    output_dir = "/home/dallas/dev/au0025l-demo"  # Default
                    dir_patterns = [
                        r"in\s+(/[\w/]+)",
                        r"directory[:\s]+([/\w]+)",
                        r"to\s+(/[\w/]+)",
                    ]
                    for pattern in dir_patterns:
                        match = re.search(pattern, user_input, re.IGNORECASE)
                        if match:
                            output_dir = match.group(1).strip()
                            break
                    
                    # Call Red Hat content creation tool
                    content_result = self.mcp_executor.execute_tool(
                        "create_redhat_content",
                        {
                            "request": user_input,
                            "output_directory": output_dir
                        },
                        context={"user_query": user_input}
                    )
                    
                    if content_result and content_result.get("success"):
                        files_created = content_result.get("files_created", {})
                        parsed_request = content_result.get("parsed_request", {})
                        
                        # Add success message to context
                        content_success_msg = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          ✅ RED HAT CONTENT CREATED SUCCESSFULLY ✅                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Topic: {parsed_request.get('topic', 'Unknown')}                            ║
║  Content Types: {', '.join(parsed_request.get('content_types', []))}        ║
║  Output Directory: {output_dir}                                              ║
║                                                                              ║
║  Files Created:                                                              ║"""
                        
                        for content_type, paths in files_created.items():
                            if isinstance(paths, dict):
                                content_success_msg += f"\n║    {content_type.upper()}:"
                                for key, path in paths.items():
                                    content_success_msg += f"\n║      - {key}: {path}"
                            else:
                                content_success_msg += f"\n║    - {content_type}: {paths}"
                        
                        content_success_msg += """
║                                                                              ║
║  ⚠️  CRITICAL: The content has ALREADY been created.                        ║
║  ⚠️  DO NOT explain how to use tools or run commands.                        ║
║  ⚠️  Simply acknowledge that the content was created successfully!           ║
║                                                                              ║
║  Your response should be like:                                              ║
║  "Done! I've created the Red Hat training content for you."                 ║
║  or "I've created the lecture, GE, and lab scripts as requested."          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
                        # Insert at beginning of context (after system prompt)
                        insert_index = 0
                        for i, part in enumerate(context_parts):
                            if "SYSTEM INSTRUCTIONS" in part or "Core Identity" in part:
                                insert_index = i + 1
                                for j in range(i, len(context_parts)):
                                    if "CONTEXT FROM OUR RELATIONSHIP" in context_parts[j] or "ADDITIONAL CONTEXT" in context_parts[j]:
                                        insert_index = j + 1
                                        break
                                break
                        context_parts.insert(insert_index, content_success_msg)
                        mcp_tools_used.append(f"create_redhat_content: {parsed_request.get('topic', 'Unknown')}")
                        state["redhat_content_created"] = files_created
                    elif content_result:
                        error = content_result.get("error", "Unknown error")
                        print(f"Red Hat content creation failed: {error}")
                        context_parts.append(f"\n\nNOTE: Attempted to create Red Hat content but encountered error: {error}")
                except Exception as e:
                    print(f"Red Hat content creation error: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Auto-detect and execute image generation if needed (works independently of MCP)
        # More specific keywords first, then general ones
        image_keywords_specific = [
        "generate an image", "create an image", "make an image", "draw an image",
        "generate a picture", "create a picture", "make a picture", "draw a picture",
        "generate image", "create image", "make image", "draw image",
        "generate picture", "create picture", "make picture", "draw picture",
        "show me an image of", "show me a picture of", "visualize", "image of",
        "picture of", "generate_image"
        ]
        # General keywords (only if combined with image/picture context)
        image_keywords_general = ["generate", "create", "make", "draw"]
        
        user_input_lower = user_input.lower()
        
        # Initialize variables
        has_general = False
        has_image_context = False
        
        # Check for specific image keywords
        needs_image = any(keyword in user_input_lower for keyword in image_keywords_specific)
        if needs_image:
            print(f"DEBUG [IMAGE DETECTION]: Image detected via specific keywords: {[kw for kw in image_keywords_specific if kw in user_input_lower]}")
        
        # Also check for general keywords + image/picture context
        if not needs_image:
            has_general = any(keyword in user_input_lower for keyword in image_keywords_general)
            has_image_context = "image" in user_input_lower or "picture" in user_input_lower or "turtle" in user_input_lower
            needs_image = has_general and has_image_context
            if needs_image:
                print(f"DEBUG [IMAGE DETECTION]: Image detected via general keywords + context (general: {has_general}, context: {has_image_context})")
        
        # Also check for direct command format: "generate_image prompt"
        if "generate_image" in user_input_lower:
            needs_image = True
            print(f"DEBUG [IMAGE DETECTION]: Image detected via 'generate_image' command")
        
        # Log if no detection
        if not needs_image:
            print(f"DEBUG [IMAGE DETECTION]: No image generation detected for input: {user_input[:100]}")
        
        # ALWAYS try to generate image if requested, even if MCP isn't available (use direct call)
        if needs_image:
            print(f"DEBUG [IMAGE DETECTION]: ✅ Image generation detected! needs_image=True for input: {user_input[:100]}")
            print(f"DEBUG [IMAGE DETECTION]: About to enter image generation block...")
            # Add a note to context that we're attempting image generation
            context_parts.insert(0, f"\n\n⚠️ USER REQUESTED IMAGE GENERATION: The user asked to create/generate an image. You MUST acknowledge this request and respond about the image generation, NOT about whether you have information about the subject matter.\n")
            # Extract image prompt from user input - improved logic
            image_prompt = user_input
            
            # Handle "generate_image" as a command
            if "generate_image" in user_input_lower:
                parts = user_input_lower.split("generate_image", 1)
                if len(parts) > 1:
                    image_prompt = parts[1].strip()
                else:
                    # If just "generate_image", try to extract from context
                    image_prompt = user_input.replace("generate_image", "").strip()
            
            # Try specific keywords first (longest first for better extraction)
            image_keywords_sorted = sorted(image_keywords_specific, key=len, reverse=True)
            for keyword in image_keywords_sorted:
                if keyword in user_input_lower:
                    parts = user_input_lower.split(keyword, 1)
                    if len(parts) > 1:
                        image_prompt = parts[1].strip()
                        break
            
            # Clean up the prompt - but preserve the full description
            # Only remove trailing question marks, not periods (they might be part of description)
            image_prompt = image_prompt.split("?")[0].strip()  # Remove question marks
            # Don't remove periods - they might be part of the description
            
            # Remove common prefixes
            for prefix in ["of", "a", "an", "the"]:
                if image_prompt.lower().startswith(prefix + " "):
                    image_prompt = image_prompt[len(prefix)+1:].strip()
            
            # If prompt is too short or same as original, try to extract better
            if len(image_prompt) < 10 or image_prompt == user_input:
                # Try to extract meaningful content - be smarter about it
                words = user_input.split()
                # Remove ONLY command/instruction words, keep descriptive words
                filtered_words = [w for w in words if w.lower() not in [
                    "alex", "generate", "create", "make", "draw", "an", "a", "image", "picture", 
                    "generate_image", "can", "you", "do", "yet", "one", "of", "the", "and"
                ]]
                if len(filtered_words) > 3:  # Only use if we have enough words
                    image_prompt = " ".join(filtered_words)
                # If still too short, use original input (might be a very short request)
                if len(image_prompt) < 5:
                    image_prompt = user_input
            
            # Ensure we have a valid prompt
            if not image_prompt or len(image_prompt.strip()) < 3:
                image_prompt = "a beautiful image"  # Fallback
            
            try:
                print(f"DEBUG: Attempting to generate image with prompt: {image_prompt}")
                image_result = None
                image_path = None
            
            # Try MCP tool first if available
                if self.mcp_executor:
                    try:
                        image_result = self.mcp_executor.execute_tool(
                            "generate_image",
                            {"prompt": image_prompt},
                            context={"user_query": user_input}
                        )
                        print(f"DEBUG: MCP Image generation result: {image_result}")
            # Check if MCP call was successful
                        if image_result and image_result.get("success"):
            # Extract image_path from MCP result
                            if isinstance(image_result.get("output"), dict):
                                image_path = image_result.get("output", {}).get("image_path")
                            elif image_result.get("image_path"):
                                image_path = image_result.get("image_path")
                    except Exception as mcp_error:
                        print(f"DEBUG: MCP tool failed, trying direct call: {mcp_error}")
                        image_result = None
            
            # ALWAYS try direct call if MCP didn't work or isn't available
                if not image_result or not image_result.get("success") or not image_path:
                    try:
                        from external_apis import ExternalAPIManager
                        api_manager = ExternalAPIManager()
            # Ensure API is registered (with token if available)
                        if "huggingface_image" not in api_manager.api_configs:
            # Try to get token from config if available
                            api_manager.register_huggingface_image_api()
            # Generate image directly
                        image_path = api_manager.generate_image(prompt=image_prompt)
                        if image_path and os.path.exists(image_path):
                            image_result = {"success": True, "image_path": image_path}
                            print(f"DEBUG: Direct image generation succeeded: {image_path}")
                        else:
                            image_result = {"success": False, "error": "Image generation returned no path"}
                    except Exception as direct_error:
                        print(f"DEBUG: Direct image generation also failed: {direct_error}")
                        import traceback
                        traceback.print_exc()
                        image_result = {"success": False, "error": str(direct_error)}
            
            # Handle different result formats
                if image_result and isinstance(image_result, dict):
            # Check for image_path in result
                    image_path = image_result.get("image_path")
                
            # Also check output field (MCP format)
                    if not image_path and image_result.get("output"):
                        output = image_result["output"]
                        if isinstance(output, dict):
                            image_path = output.get("image_path")
                        elif isinstance(output, str) and os.path.exists(output):
                            image_path = output
                
            # Check success status
                    success = image_result.get("success", False)
                
                    if success and image_path and os.path.exists(image_path):
            # Put this at the VERY TOP of context so it's impossible to miss
                        image_success_msg = f"""
                        ╔══════════════════════════════════════════════════════════════════════════════╗
                        ║                    ✅ IMAGE GENERATED SUCCESSFULLY ✅                        ║
                        ╠══════════════════════════════════════════════════════════════════════════════╣
                        ║  The image has ALREADY been generated and saved to:                         ║
                        ║  {image_path}                                                                ║
                        ║                                                                              ║
                        ║  Prompt used: {image_prompt[:100]}...                                       ║
                        ║                                                                              ║
                        ║  ⚠️  CRITICAL: DO NOT explain how to use tools.                             ║
                        ║  ⚠️  DO NOT tell the user to run commands.                                  ║
                        ║  ⚠️  The image is ALREADY created - just acknowledge it naturally!          ║
                        ║                                                                              ║
                        ║  Your response should be simple, like:                                       ║
                        ║  "Done! I've created that image for you."                                   ║
                        ║  or "Here's your image!"                                                     ║
                        ╚══════════════════════════════════════════════════════════════════════════════╝
                        """
                        # Insert at the beginning of context_parts (after system prompt)
                        # Find where to insert (after system prompt section)
                        insert_index = 0
                        for i, part in enumerate(context_parts):
                            if "SYSTEM INSTRUCTIONS" in part or "Core Identity" in part:
                                insert_index = i + 1
                                # Find the end of system prompt section
                                for j in range(i, len(context_parts)):
                                    if "CONTEXT FROM OUR RELATIONSHIP" in context_parts[j] or "ADDITIONAL CONTEXT" in context_parts[j]:
                                        insert_index = j + 1
                                        break
                                break
                            
                        context_parts.insert(insert_index, image_success_msg)
                        # Track tool usage (initialize if not exists)
                        if 'mcp_tools_used' not in locals():
                            mcp_tools_used = []
                        mcp_tools_used.append(f"generate_image: {image_prompt}")
                        state["generated_image"] = image_path
                    elif not success:
                        error = image_result.get("error", "Unknown error")
                        print(f"Image generation failed: {error}")
                        context_parts.append(f"\n\nNOTE: Attempted to generate image but encountered error: {error}")
                    else:
                        print(f"Image generation completed but no valid path found in result")
                        context_parts.append(f"\n\nNOTE: Attempted to generate image with prompt '{image_prompt}' but no image path was returned")
                elif isinstance(image_result, str) and os.path.exists(image_result):
                    # Result is direct path string
                    image_path = image_result
                    image_success_msg = f"""
                    ╔══════════════════════════════════════════════════════════════════════════════╗
                    ║                    ✅ IMAGE GENERATED SUCCESSFULLY ✅                        ║
                    ╠══════════════════════════════════════════════════════════════════════════════╣
                    ║  The image has ALREADY been generated and saved to:                         ║
                    ║  {image_path}                                                                ║
                    ║                                                                              ║
                    ║  ⚠️  CRITICAL: DO NOT explain how to use tools.                             ║
                    ║  ⚠️  DO NOT tell the user to run commands.                                  ║
                    ║  ⚠️  The image is ALREADY created - just acknowledge it naturally!          ║
                    ╚══════════════════════════════════════════════════════════════════════════════╝
                    """
                    # Insert at beginning of context
                    insert_index = 0
                    for i, part in enumerate(context_parts):
                        if "SYSTEM INSTRUCTIONS" in part or "Core Identity" in part:
                            insert_index = i + 1
                            for j in range(i, len(context_parts)):
                                if "CONTEXT FROM OUR RELATIONSHIP" in context_parts[j] or "ADDITIONAL CONTEXT" in context_parts[j]:
                                    insert_index = j + 1
                                    break
                            break
                    context_parts.insert(insert_index, image_success_msg)
                    state["generated_image"] = image_path
                        
            except Exception as e:
            # If tool call fails, log and continue
                import traceback
                error_details = traceback.format_exc()
                print(f"DEBUG [IMAGE GENERATION]: Outer exception caught: {e}")
                print(f"DEBUG [IMAGE GENERATION]: Traceback: {error_details}")
            # Still try direct call as last resort
                try:
                    print(f"DEBUG [IMAGE GENERATION]: Attempting fallback direct API call...")
                    from external_apis import ExternalAPIManager
                    api_manager = ExternalAPIManager()
                    if "huggingface_image" not in api_manager.api_configs:
                        api_manager.register_huggingface_image_api()
                    image_path = api_manager.generate_image(prompt=image_prompt)
                    if image_path:
                        print(f"DEBUG [IMAGE GENERATION]: Fallback succeeded! Image at: {image_path}")
                        image_success_msg = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ✅ IMAGE GENERATED SUCCESSFULLY ✅                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  The image has ALREADY been generated and saved to:                         ║
║  {image_path}                                                                ║
║                                                                              ║
║  Prompt used: {image_prompt[:100]}...                                       ║
║                                                                              ║
║  ⚠️  CRITICAL: DO NOT explain how to use tools.                             ║
║  ⚠️  DO NOT tell the user to run commands.                                  ║
║  ⚠️  The image is ALREADY created - just acknowledge it naturally!          ║
║                                                                              ║
║  Your response should be simple, like:                                       ║
║  "Done! I've created that image for you."                                   ║
║  or "Here's your image!"                                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
                        insert_index = 0
                        for i, part in enumerate(context_parts):
                            if "SYSTEM INSTRUCTIONS" in part or "Core Identity" in part:
                                insert_index = i + 1
                                for j in range(i, len(context_parts)):
                                    if "CONTEXT FROM OUR RELATIONSHIP" in context_parts[j] or "ADDITIONAL CONTEXT" in context_parts[j]:
                                        insert_index = j + 1
                                        break
                                break
                        context_parts.insert(insert_index, image_success_msg)
                        state["generated_image"] = image_path
                    else:
                        print(f"DEBUG [IMAGE GENERATION]: Fallback returned no image path")
                        context_parts.insert(0, f"\n\n⚠️ IMAGE GENERATION ATTEMPTED: User requested image generation with prompt '{image_prompt}', but generation failed with error: {str(e)}. Please acknowledge that you attempted to generate the image but encountered an issue.")
                except Exception as final_error:
                    print(f"DEBUG [IMAGE GENERATION]: Fallback also failed: {final_error}")
                    import traceback
                    traceback.print_exc()
                    context_parts.insert(0, f"\n\n⚠️ IMAGE GENERATION ATTEMPTED: User requested image generation with prompt '{image_prompt}', but tool execution failed: {str(e)}. Please acknowledge that you attempted to generate the image but encountered an issue.")
        
        full_context = "\n".join(context_parts)
        
        # Add strict instructions to prevent hallucination - make it VERY prominent
        anti_hallucination_instruction = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CRITICAL: ANTI-HALLUCINATION RULES                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ 1. Use ONLY the information provided above. DO NOT invent, make up, or      ║
║    guess facts.                                                               ║
║ 2. If information is not provided, say "I don't have that information"       ║
║    rather than guessing or inventing.                                        ║
║ 3. Do NOT create fictional timelines, relationships, biographical details,   ║
║    academic essays, or random stories.                                       ║
║ 4. Do NOT respond with "Tell me something from my history!" - respond       ║
║    directly to what the user asked.                                          ║
║ 5. Stay focused on being a helpful personal assistant.                       ║
║ 6. If unsure, say you don't know rather than making something up.            ║
║ 7. Base your response ONLY on actual data provided in context sections.     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        # Add instruction to use web search results if available
        if web_search_results:
            full_prompt = f"{full_context}\n\n{anti_hallucination_instruction}\n\nIMPORTANT: Use the web search results above to answer the user's question. Cite the sources when relevant.\n\nUser: {user_input}\nAssistant:"
        else:
            full_prompt = f"{full_context}\n\n{anti_hallucination_instruction}\n\nUser: {user_input}\nAssistant:"
        
        # Generate response using Ollama
        try:
            # Validate model_name is not empty
            if not self.model_name or not self.model_name.strip():
                state["response"] = (
                    f"Error: Model name is empty or not set. "
                    f"Please check your config.json and ensure 'model_name' is set correctly."
                )
                return state
            
            # Check if model is available
            try:
                from ollama import list as ollama_list
                try:
                    models_response = ollama_list()
                except Exception as api_error:
                    # Connection or API error
                    raise ValueError(
                        f"Failed to call Ollama list API: {str(api_error)}. "
                        f"Make sure Ollama is running: ollama serve"
                    ) from api_error
                
                # Handle different response formats
                models_list = []
                if isinstance(models_response, dict):
                    # Standard format: {"models": [...]}
                    models_list = models_response.get("models", [])
                elif isinstance(models_response, list):
                    # Direct list format
                    models_list = models_response
                elif models_response is None:
                    raise ValueError("Ollama API returned None. Is Ollama running?")
                else:
                    # Try to extract models anyway
                    if hasattr(models_response, 'models'):
                        models_list = models_response.models
                    elif hasattr(models_response, '__iter__'):
                        models_list = list(models_response)
                    else:
                        # Include repr of response for debugging (limit length)
                        response_repr = repr(models_response)
                        if len(response_repr) > 200:
                            response_repr = response_repr[:200] + "..."
                        raise ValueError(
                            f"Unexpected Ollama API response format: {type(models_response)}. "
                            f"Expected dict with 'models' key or list. "
                            f"Response type: {type(models_response).__name__}, "
                            f"Response value (first 200 chars): {response_repr}"
                        )
                
                if not isinstance(models_list, list):
                    raise ValueError(f"Models list is not a list: {type(models_list)}")
                
                # Check if models_list is empty
                if len(models_list) == 0:
                    # This might be valid - user might not have any models
                    # But let's provide helpful debug info
                    debug_info = []
                    debug_info.append(f"Response type: {type(models_response).__name__}")
                    if isinstance(models_response, dict):
                        debug_info.append(f"Response keys: {list(models_response.keys())}")
                        for key in models_response.keys():
                            val = models_response[key]
                            debug_info.append(f"  {key}: {type(val).__name__} (length: {len(val) if hasattr(val, '__len__') else 'N/A'})")
                    debug_info.append(f"Models list is empty - this might be normal if no models are pulled")
                    
                    state["response"] = (
                        f"Error: No models found in Ollama (models list is empty). "
                        f"\n\nDebug: {'; '.join(debug_info)}"
                        f"\n\nPlease ensure you have pulled at least one model: ollama pull {self.model_name}"
                    )
                    return state
                
                # Helper function to extract model name string from any format
                def extract_model_name(model_obj):
                    """Extract model name string from dict, string, or Model object"""
                    if isinstance(model_obj, str):
                        return model_obj.strip()
                    elif isinstance(model_obj, dict):
                        # Try multiple possible keys for model name
                        name = model_obj.get("name") or model_obj.get("model") or model_obj.get("model_name") or ""
                        if name and isinstance(name, str):
                            return name.strip()
                        elif name:
                            return str(name).strip()
                    else:
                        # Try to extract name from Model object or other objects
                        # Model objects from ollama have a 'model' attribute
                        if hasattr(model_obj, 'model'):
                            model_attr = getattr(model_obj, 'model')
                            if model_attr and isinstance(model_attr, str):
                                return model_attr.strip()
                        if hasattr(model_obj, 'name'):
                            name_attr = getattr(model_obj, 'name')
                            if name_attr:
                                name_str = str(name_attr).strip()
                                if name_str:
                                    return name_str
                    return None
                
                model_names = []
                for idx, m in enumerate(models_list):
                    name = extract_model_name(m)
                    if name:
                        model_names.append(name)
                
                # Remove duplicates while preserving order
                seen = set()
                model_names = [m for m in model_names if not (m in seen or seen.add(m))]
                
                if not model_names:
                    # Debug: show what we got
                    debug_info = []
                    debug_info.append(f"Models list type: {type(models_list)}")
                    debug_info.append(f"Models list length: {len(models_list)}")
                    if models_list:
                        debug_info.append(f"First item type: {type(models_list[0])}")
                        debug_info.append(f"First item: {repr(models_list[0])[:200]}")
                    if isinstance(models_response, dict):
                        debug_info.append(f"Response keys: {list(models_response.keys())}")
                    
                    state["response"] = (
                        f"Error: No models found in Ollama after parsing. "
                        f"\n\nDebug info: {'; '.join(debug_info)}"
                        f"\n\nPlease ensure:"
                        f"\n1. Ollama is running: ollama serve"
                        f"\n2. You have models: ollama list"
                        f"\n3. Pull a model: ollama pull {self.model_name}"
                    )
                    return state
                
                # Normalize self.model_name for comparison (preserve original)
                # First, ensure self.model_name is a string, not a Model object
                original_model_name = self.model_name
                
                # Extract string from self.model_name if it's an object
                if not isinstance(self.model_name, str):
                    # Try to extract the model name string from the object
                    extracted_name = extract_model_name(self.model_name)
                    if extracted_name:
                        self.model_name = extracted_name
                    else:
                        state["response"] = (
                            f"Error: Cannot extract model name from object. "
                            f"Type: {type(self.model_name)}, "
                            f"Value: {repr(self.model_name)[:200]}. "
                            f"Please check your config.json and ensure 'model_name' is set to a string."
                        )
                        return state
                
                # Ensure self.model_name is valid after extraction
                if not self.model_name or not isinstance(self.model_name, str) or not self.model_name.strip():
                    state["response"] = (
                        f"Error: Model name is empty or invalid after extraction. "
                        f"Original type: {type(original_model_name)}, "
                        f"Extracted: {repr(self.model_name)}. "
                        f"Please check your config.json and ensure 'model_name' is set correctly."
                    )
                    return state
                
                normalized_model_name = self.model_name.strip() if self.model_name else ""
                
                # Ensure normalized name is not empty before proceeding
                if not normalized_model_name:
                    state["response"] = (
                        f"Error: Model name is empty after normalization. "
                        f"Original: {repr(original_model_name)}. "
                        f"Please check your config.json and ensure 'model_name' is set correctly."
                    )
                    return state
                
                self.model_name = normalized_model_name
                
                # Check for exact match first
                if self.model_name not in model_names:
                    # Try case-insensitive exact match
                    model_lower = self.model_name.lower()
                    matching_models = [m for m in model_names if m.lower() == model_lower]
                    
                    matched = False
                    if matching_models:
                        # Found a case-insensitive match, use it
                        # matching_models contains strings from model_names, so this should be safe
                        actual_model_name = matching_models[0].strip() if matching_models[0] else None
                        # Update model_name for this session only if valid and non-empty
                        # Ensure it's a string (should already be, but double-check)
                        if actual_model_name and isinstance(actual_model_name, str) and actual_model_name.strip():
                            self.model_name = actual_model_name.strip()
                            matched = True
                    
                    if not matched:
                        # Try flexible matching:
                        # 1. Base name match (e.g., "llama3.2:3b" matches "llama3.2" or "llama3.2:latest")
                        # 2. Partial match (e.g., "phi3:mini" matches "phi3-mini")
                        partial_matches = []
                        model_base = self.model_name.split(':')[0].lower().strip()
                        
                        # Only proceed if model_base is not empty
                        if model_base:
                            for m in model_names:
                                if not m or not m.strip():
                                    continue
                                m_lower = m.lower()
                                m_base = m.split(':')[0].lower().strip()
                                
                                # Exact base match (preferred)
                                if model_base == m_base:
                                    partial_matches.insert(0, m)  # Prioritize exact base matches
                                # Base name contains or is contained in model name
                                elif model_base in m_lower or m_base in model_base:
                                    partial_matches.append(m)
                        
                        if partial_matches and partial_matches[0]:
                            # Automatically use the first (best) partial match instead of erroring
                            # partial_matches contains strings from model_names, so this should be safe
                            actual_model_name = partial_matches[0].strip() if partial_matches[0] else ""
                            # Validate the matched model name is not empty and is a string
                            if actual_model_name and isinstance(actual_model_name, str) and actual_model_name.strip():
                                # Update model_name for this session - ensure it's a clean string
                                self.model_name = actual_model_name.strip()
                                # Continue with the matched model
                            else:
                                # Fall through to error
                                partial_matches = []
                        else:
                            # No matches at all
                            all_models_str = ', '.join(model_names) if model_names else "none"
                            state["response"] = (
                                f"Error: Model '{self.model_name}' not found. "
                                f"\n\nAvailable models: {all_models_str}"
                                f"\n\nPlease run: ollama pull {self.model_name}"
                                f"\n\nOr update config.json to use one of the available models above."
                            )
                            return state
            except Exception as e:
                import traceback
                error_details = str(e)
                # Include more context in error message
                if "Unexpected" in error_details or "None" in error_details:
                    error_msg = (
                        f"Error: Cannot connect to Ollama or unexpected response format. "
                        f"\n\nDetails: {error_details}"
                        f"\n\nPlease ensure:"
                        f"\n1. Ollama is running: ollama serve"
                        f"\n2. Ollama is accessible: ollama list"
                        f"\n3. You have at least one model pulled: ollama pull {self.model_name}"
                    )
                else:
                    error_msg = (
                        f"Error: Cannot connect to Ollama. "
                        f"Please ensure Ollama is running: ollama serve. "
                        f"\n\nError: {error_details}"
                    )
                state["response"] = error_msg
                return state
            
            # Final validation before making API call - be very strict
            # Ensure self.model_name is a string, not a Model object
            if not isinstance(self.model_name, str):
                # Try to extract string from Model object
                if hasattr(self.model_name, 'model'):
                    model_attr = getattr(self.model_name, 'model')
                    if model_attr and isinstance(model_attr, str):
                        self.model_name = model_attr.strip()
                    else:
                        state["response"] = (
                            f"Error: self.model_name is not a string. "
                            f"Type: {type(self.model_name)}, "
                            f"Value: {repr(self.model_name)[:200]}. "
                            f"Please check your config.json and ensure 'model_name' is set to a string."
                        )
                        return state
                else:
                    state["response"] = (
                        f"Error: self.model_name is not a string and cannot extract model name. "
                        f"Type: {type(self.model_name)}, "
                        f"Value: {repr(self.model_name)[:200]}. "
                        f"Please check your config.json and ensure 'model_name' is set to a string."
                    )
                    return state
            
            # Helper function to extract model name string (handles Model objects)
            def extract_model_string(val):
                """Extract model name string from string or Model object"""
                if isinstance(val, str):
                    return val.strip() if val.strip() else None
                elif hasattr(val, 'model'):
                    model_attr = getattr(val, 'model')
                    if model_attr and isinstance(model_attr, str):
                        return model_attr.strip()
                return None
            
            # Extract model_name_to_use as a string (handles Model objects)
            model_name_to_use = extract_model_string(self.model_name)
            if not model_name_to_use:
                state["response"] = (
                    f"Error: Cannot extract model name string. "
                    f"self.model_name type: {type(self.model_name)}, "
                    f"self.model_name value: {repr(self.model_name)[:200]}. "
                    f"Please check your config.json and ensure 'model_name' is set correctly."
                )
                return state
            
            # Ensure it's a string (should be after extraction, but double-check)
            if not isinstance(model_name_to_use, str) or not model_name_to_use.strip():
                state["response"] = (
                    f"Error: Model name is not a valid string after extraction. "
                    f"Type: {type(model_name_to_use)}, "
                    f"Value: {repr(model_name_to_use)}. "
                    f"Please check your config.json and ensure 'model_name' is set correctly."
                )
                return state
            
            # Try streaming first, fallback to non-streaming if needed
            try:
                # Final validation - ensure model is a string and not empty
                # model_name_to_use should already be a string, but verify
                if not isinstance(model_name_to_use, str):
                    model_name_to_use = extract_model_string(model_name_to_use) or extract_model_string(self.model_name)
                    if not model_name_to_use or not isinstance(model_name_to_use, str):
                        raise ValueError(
                            f"Cannot extract model name string. "
                            f"model_name_to_use type: {type(model_name_to_use)}, "
                            f"self.model_name type: {type(self.model_name)}"
                        )
                
                final_model_name = model_name_to_use.strip()
                if not final_model_name:
                    raise ValueError(
                        f"Model name is empty after strip. "
                        f"model_name_to_use: {repr(model_name_to_use)}"
                    )
                
                stream = chat(
                    model=final_model_name,
                    messages=[{"role": "system", "content": full_prompt}],
                    stream=True,
                )
                
                response = ""
                chunk_count = 0
                empty_chunks = 0
                for chunk in stream:
                    content = None
                    if "message" in chunk and "content" in chunk["message"]:
                        content = chunk["message"]["content"]
                    elif "content" in chunk:  # Alternative format
                        content = chunk["content"]
                    elif "delta" in chunk and "content" in chunk["delta"]:
                        # Some Ollama versions use delta format
                        content = chunk["delta"]["content"]
                    
                    if content:
                        response += content
                        chunk_count += 1
                    else:
                        empty_chunks += 1
                
                # Debug: Log streaming response
                if not response or not response.strip():
                    print(f"DEBUG: Empty response from streaming for model '{final_model_name}'")
                    print(f"DEBUG: Received {chunk_count} chunks with content, {empty_chunks} empty chunks")
                    if chunk_count == 0:
                        print(f"DEBUG: No content chunks received - stream may have failed silently")
                
                # Filter out thinking tokens if suppress_thinking is enabled
                # But preserve the response if filtering removes everything
                if self.suppress_thinking and response:
                    original_response = response
                    filtered = self._filter_thinking_tokens(response)
                    # Only use filtered version if it's not empty
                    if filtered and filtered.strip():
                        response = filtered
                    # If filtering removed everything, keep original
                    elif not filtered or not filtered.strip():
                        response = original_response
                        print(f"DEBUG: Thinking filter removed all content from streaming, keeping original")
            except Exception as stream_error:
                # Fallback to non-streaming
                try:
                    # Helper to extract string from model name (handles Model objects)
                    def get_model_string(model_val):
                        """Extract model name string, handling Model objects"""
                        if isinstance(model_val, str):
                            return model_val.strip() if model_val.strip() else None
                        elif hasattr(model_val, 'model'):
                            model_attr = getattr(model_val, 'model')
                            if model_attr and isinstance(model_attr, str):
                                return model_attr.strip()
                        return None
                    
                    # Re-validate and get model name - try multiple sources
                    final_model_name = None
                    
                    # Helper function (redefined here for clarity)
                    def get_model_string(val):
                        """Extract model name string, handling Model objects"""
                        if isinstance(val, str):
                            return val.strip() if val.strip() else None
                        elif hasattr(val, 'model'):
                            model_attr = getattr(val, 'model')
                            if model_attr and isinstance(model_attr, str):
                                return model_attr.strip()
                        return None
                    
                    # Try model_name_to_use first (extract string if it's a Model object)
                    if model_name_to_use:
                        final_model_name = get_model_string(model_name_to_use)
                    
                    # Fall back to self.model_name (extract string if it's a Model object)
                    if not final_model_name and self.model_name:
                        final_model_name = get_model_string(self.model_name)
                    
                    # Last resort: try to get from config
                    if not final_model_name:
                        try:
                            config_path = "config.json"
                            if os.path.exists(config_path):
                                with open(config_path, "r") as f:
                                    config = json.load(f)
                                    config_model = config.get("model_name", "").strip()
                                    if config_model:
                                        final_model_name = config_model
                        except:
                            pass
                    
                    # If we still don't have a model name, raise an error
                    if not final_model_name or not isinstance(final_model_name, str):
                        raise ValueError(
                            f"Model name is None or not a string. "
                            f"model_name_to_use: {repr(model_name_to_use)}, "
                            f"self.model_name: {repr(self.model_name)}, "
                            f"final_model_name: {repr(final_model_name)}. "
                            f"Please check your config.json and ensure 'model_name' is set correctly."
                        )
                    
                    # Strip and validate - ensure it's not empty after stripping
                    final_model_name = final_model_name.strip()
                    if not final_model_name:
                        raise ValueError(
                            f"Model name is empty after stripping. "
                            f"Before strip: {repr(final_model_name if 'final_model_name' in locals() else 'not set')}, "
                            f"model_name_to_use: {repr(model_name_to_use)}, "
                            f"self.model_name: {repr(self.model_name)}. "
                            f"Please check your config.json and ensure 'model_name' is set correctly."
                        )
                    
                    # Absolute final check - ensure model is never None or empty
                    if not final_model_name:
                        raise ValueError(
                            f"CRITICAL: Model name is empty right before chat() call. "
                            f"This should never happen. "
                            f"final_model_name: {repr(final_model_name)}"
                        )
                    
                    # Use the validated final_model_name - ensure it's passed correctly
                    # Double-check the model parameter is not None/empty
                    model_param = final_model_name if final_model_name else None
                    if not model_param:
                        raise ValueError("Model parameter cannot be None or empty")
                    
                    result = chat(
                        model=model_param,
                        messages=[{"role": "system", "content": full_prompt}],
                        stream=False,
                    )
                    
                    # Extract response with better error handling
                    response = ""
                    if result:
                        if isinstance(result, dict):
                            if "message" in result and isinstance(result["message"], dict):
                                response = result["message"].get("content", "")
                            elif "content" in result:
                                response = result["content"]
                            else:
                                # Debug: log what we got
                                print(f"DEBUG: Unexpected result structure: {list(result.keys())}")
                                response = str(result)
                        elif isinstance(result, str):
                            response = result
                        else:
                            response = str(result)
                    
                    # Debug: Log if response is empty before filtering
                    if not response or not response.strip():
                        print(f"DEBUG: Empty response from model '{model_param}' before filtering")
                        print(f"DEBUG: Result type: {type(result)}, Result: {result}")
                    
                    # Filter out thinking tokens if suppress_thinking is enabled
                    # But preserve the response if filtering removes everything
                    if self.suppress_thinking and response:
                        original_response = response
                        filtered = self._filter_thinking_tokens(response)
                        # Only use filtered version if it's not empty
                        if filtered and filtered.strip():
                            response = filtered
                        # If filtering removed everything, keep original (might be a false positive)
                        elif not filtered or not filtered.strip():
                            # Keep original response if filtering removed everything
                            # This prevents false positives where the filter removes valid content
                            response = original_response
                            print(f"DEBUG: Thinking filter removed all content, keeping original response")
                except Exception as e:
                    # Include detailed error information
                    error_details = (
                        f"Both streaming and non-streaming failed.\n"
                        f"Streaming error: {stream_error}\n"
                        f"Non-streaming error: {e}\n"
                        f"model_name_to_use: {repr(model_name_to_use)}\n"
                        f"self.model_name: {repr(self.model_name)}\n"
                        f"final_model_name (attempted): {repr(final_model_name if 'final_model_name' in locals() else 'not set')}"
                    )
                    raise Exception(error_details)
            
            # Check if we got any response
            if not response or response.strip() == "":
                state["response"] = (
                    f"Error: Model '{self.model_name}' returned an empty response. "
                    f"This might indicate the model is not responding properly. "
                    f"Try: ollama pull {self.model_name} or check model status."
                )
            else:
                state["response"] = response
            
            # Store data source tracking in state for logging
            if "data_sources" not in state:
                state["data_sources"] = {}
            state["data_sources"]["rag_files"] = rag_files_used if 'rag_files_used' in locals() else []
            state["data_sources"]["journal_entries"] = journal_entries_used if 'journal_entries_used' in locals() else []
            state["data_sources"]["mcp_tools"] = mcp_tools_used if 'mcp_tools_used' in locals() else []
            # Add local services data sources (calendar, reminders, tasks)
            # Always store local_services_data if it exists (even if empty) for proper logging
            if 'local_services' in locals():
                state["data_sources"]["local_services"] = local_services
            elif 'local_services_data' in locals():
                state["data_sources"]["local_services"] = local_services_data
            
            # Add to messages
            if "messages" not in state:
                state["messages"] = []
            state["messages"].append({"role": "user", "content": user_input})
            state["messages"].append({"role": "assistant", "content": state["response"]})
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            state["response"] = (
                f"I apologize, but I encountered an error: {str(e)}\n\n"
                f"Details: {error_details[:500]}"
            )
        
        return state
    
    def store_memory(self, state: AgentState) -> AgentState:
        """Store this interaction in memory"""
        user_input = state.get("user_input", "")
        response = state.get("response", "")
        user_sentiment = state.get("user_sentiment", 0.0)
        context = state.get("context", {})
        
        # Calculate importance (can be enhanced)
        importance = self._calculate_importance(user_input, response, context)
        
        # Store episodic memory with persona context to prevent cross-contamination
        persona_name = "default"
        if self.sona_path:
            try:
                with open(self.sona_path, 'r') as f:
                    sona_data = json.load(f)
                    persona_name = sona_data.get("name", os.path.basename(self.sona_path).replace(".json", ""))
            except:
                persona_name = os.path.basename(self.sona_path).replace(".json", "") if self.sona_path else "default"
        
        memory_id = self.memory.remember_episodic(
            content=f"User: {user_input}\nAssistant: {response}",
            context=json.dumps(context),
            importance=importance,
            tags=context.get("topics", []),
            relationship_context=f"conversation|persona:{persona_name}"
        )
        
        # Note: Emotional memory tracking removed - this is a business tool
        
        # Extract and store semantic facts
        self._extract_and_store_facts(user_input, response, memory_id)
        
        # Update journal if available
        if self.journal:
            # Extract biographical information from conversation
            self.journal.extract_from_conversation(user_input)
            # Save journal
            self.journal.save_journal()
        
        # Check for media attachments in context
        if state.get("context", {}).get("has_media"):
            media_files = state.get("context", {}).get("media_files", [])
            for media_file in media_files:
                media_type = media_file.get("type", "unknown")
                file_path = media_file.get("path")
                if file_path and os.path.exists(file_path):
                    description = media_file.get("description", "")
                    self.memory.remember_media(
                        memory_id=memory_id,
                        media_type=media_type,
                        file_path=file_path,
                        description=description
                    )
        
        return state
    
    def adapt_personality(self, state: AgentState) -> AgentState:
        """Adapt personality based on this interaction"""
        user_sentiment = state.get("user_sentiment", 0.0)
        response = state.get("response", "")
        context = state.get("context", {})
        
        # Determine response type (simplified)
        response_type = "neutral"
        if "!" in response or "😊" in response or "😄" in response:
            response_type = "humor_appreciated"
        elif len(response) < 50:
            response_type = "direct_preferred"
        
        interaction_context = {
            "user_sentiment": user_sentiment,
            "response_type": response_type,
            "topic": context.get("topics", ["general"])[0] if context.get("topics") else "general"
        }
        
        self.personality.adapt_personality(interaction_context)
        
        # Update relationship dynamics
        if user_sentiment > 0.5:
            self.personality.update_relationship_dynamic("closeness", 0.01)
        elif user_sentiment < -0.5:
            self.personality.update_relationship_dynamic("trust", -0.01)
        
        return state
    
    def check_proactivity(self, state: AgentState) -> AgentState:
        """Check if Mo11y should proactively engage"""
        suggestions = self.personality.get_proactive_suggestions()
        
        # Only proact occasionally (10% chance) to avoid being annoying
        import random
        should_proact = len(suggestions) > 0 and random.random() < 0.1
        
        state["should_proact"] = should_proact
        state["proactivity_suggestions"] = suggestions
        
        return state
    
    def _estimate_sentiment(self, text: str) -> float:
        """Simple sentiment estimation (can be enhanced with proper NLP)"""
        positive_words = ["happy", "great", "love", "wonderful", "amazing", "good", "yes", "thanks", "thank"]
        negative_words = ["sad", "bad", "hate", "terrible", "awful", "no", "angry", "frustrated", "disappointed"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return min(1.0, 0.3 + (positive_count * 0.2))
        elif negative_count > positive_count:
            return max(-1.0, -0.3 - (negative_count * 0.2))
        return 0.0
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics/keywords from text (simplified)"""
        # Simple keyword extraction (can be enhanced with NLP)
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "can"}
        
        words = text.lower().split()
        topics = [w for w in words if len(w) > 3 and w not in common_words][:5]
        return topics
    
    def _calculate_importance(self, user_input: str, response: str, context: Dict) -> float:
        """Calculate importance score for memory"""
        importance = 0.5  # Base importance
        
        # Increase if question mark (shows engagement)
        if context.get("has_question"):
            importance += 0.1
        
        # Increase if emotional
        sentiment = abs(context.get("user_sentiment", 0.0))
        importance += sentiment * 0.2
        
        # Increase if long conversation
        if len(user_input) > 100:
            importance += 0.1
        
        return min(1.0, importance)
    
    def _filter_thinking_tokens(self, text: str) -> str:
        """
        Filter out thinking/reasoning tokens from model output.
        Specifically handles deepseek-r1 and other reasoning models.
        Only removes actual thinking tokens, not regular conversational content.
        """
        import re
        
        # If text is empty or very short, don't filter (might be a false positive)
        if not text or len(text.strip()) < 10:
            return text
        
        original_text = text
        
        # DeepSeek-R1 and similar models use various formats for thinking tokens
        # Remove XML-style thinking tags (most common format)
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<reasoning>.*?</reasoning>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<thought>.*?</thought>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<reflection>.*?</reflection>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove bracket-style thinking tags
        text = re.sub(r'\[THINKING\].*?\[/THINKING\]', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'\[REASONING\].*?\[/REASONING\]', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'\[THOUGHT\].*?\[/THOUGHT\]', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Only remove thinking blocks if they're clearly marked as thinking
        # Be more conservative - only remove if there's clear thinking tag structure
        # Don't remove conversational phrases that might be part of normal responses
        
        # Remove any remaining XML-like tags that might have been missed
        text = re.sub(r'<[^>]*think[^>]*>.*?</[^>]*think[^>]*>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple blank lines to double
        text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)  # Remove leading whitespace from lines
        text = text.strip()
        
        # Safety check: If filtering removed more than 90% of content, it's probably a false positive
        # Return original text to prevent removing valid responses
        if len(text) < len(original_text) * 0.1 and len(original_text) > 20:
            print(f"DEBUG: Thinking filter removed too much content ({len(text)}/{len(original_text)} chars), keeping original")
            return original_text
        
        return text
    
    def _extract_and_store_facts(self, user_input: str, response: str, memory_id: int):
        """Extract facts from conversation and store as semantic memories"""
        # Simple fact extraction (can be enhanced)
        facts = []
        
        # Look for "I am", "I like", "I have" patterns
        if "i am" in user_input.lower() or "i'm" in user_input.lower():
            # Extract fact after "I am"
            parts = user_input.lower().split("i am")[-1].split("i'm")[-1].split(".")[0].strip()
            if len(parts) > 5:
                facts.append(("user_trait", parts))
        
        if "i like" in user_input.lower():
            parts = user_input.lower().split("i like")[-1].split(".")[0].strip()
            if len(parts) > 3:
                facts.append(("user_preference", parts))
        
        # Store facts
        for fact_type, fact_value in facts:
            self.memory.remember_semantic(
                key=f"{fact_type}_{hash(fact_value) % 10000}",
                value=fact_value,
                confidence=0.7,
                source_memory_id=memory_id
            )
    
    def _load_redhat_instructions(self) -> Optional[str]:
        """
        Load Red Hat instruction files (lectures.md, guided-exercises.md) from redhat-content-standards directory
        Returns formatted text with instruction content, or None if not available
        """
        try:
            # Try to get standards directory from config
            config_path = "config.json"
            standards_dir = None
            
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    redhat_config = config.get("redhat_content", {})
                    standards_dir = redhat_config.get("standards_dir")
            
            if not standards_dir or not os.path.exists(standards_dir):
                return None
            
            instructions_dir = os.path.join(standards_dir, "instructions")
            if not os.path.exists(instructions_dir):
                return None
            
            # Load instruction files
            instructions = []
            instruction_files = [
                ("lectures.md", "Lecture Development Instructions"),
                ("guided-exercises.md", "Guided Exercise Development Instructions")
            ]
            
            for filename, title in instruction_files:
                file_path = os.path.join(instructions_dir, filename)
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            instructions.append(f"\n{title}:\n{'='*60}\n{content}\n")
                    except Exception as e:
                        print(f"Warning: Could not load instruction file {filename}: {e}")
                        continue
            
            if instructions:
                return "\n".join(instructions)
            return None
            
        except Exception as e:
            print(f"Warning: Could not load Red Hat instructions: {e}")
            return None
    
    def _load_redhat_style_guides(self) -> Optional[str]:
        """
        Load Red Hat style guides from redhat-content-standards directory
        Returns formatted text with style guide content, or None if not available
        """
        try:
            # Try to get standards directory from config
            config_path = "config.json"
            standards_dir = None
            
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    redhat_config = config.get("redhat_content", {})
                    standards_dir = redhat_config.get("standards_dir")
            
            if not standards_dir or not os.path.exists(standards_dir):
                return None
            
            style_guides_dir = os.path.join(standards_dir, "style-guides")
            if not os.path.exists(style_guides_dir):
                return None
            
            # Load all style guide files
            style_guides = []
            guide_files = [
                ("asciidoc-formatting.md", "AsciiDoc Formatting Guide"),
                ("content-structure.md", "Content Structure Guide"),
                ("writing-style.md", "Writing Style Guide")
            ]
            
            for filename, title in guide_files:
                file_path = os.path.join(style_guides_dir, filename)
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            style_guides.append(f"\n{title}:\n{'='*60}\n{content}\n")
                    except Exception as e:
                        print(f"Warning: Could not load style guide {filename}: {e}")
                        continue
            
            # Also load instruction files for callout details
            instructions_dir = os.path.join(standards_dir, "instructions")
            if os.path.exists(instructions_dir):
                instruction_files = [
                    ("lectures.md", "Lecture Instructions (includes callout details)"),
                    ("guided-exercises.md", "Guided Exercise Instructions (includes callout details)")
                ]
                for filename, title in instruction_files:
                    file_path = os.path.join(instructions_dir, filename)
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                                # Extract callout section if present
                                if "callout" in content.lower() or "Callout" in content:
                                    style_guides.append(f"\n{title}:\n{'='*60}\n{content}\n")
                        except Exception as e:
                            print(f"Warning: Could not load instruction file {filename}: {e}")
                            continue
            
            if style_guides:
                # Add AsciiDoc callout syntax reference based on Red Hat standards
                callout_info = """
                
                RED HAT CALLOUT FORMAT (from style guides):
                ==============================================
                Callouts are used to explain content in example files and YAML manifests:
                
                Format:
                1. Use callout numbers in angle brackets (<1>, <2>, <3>, etc.) INSIDE the code block
                2. After the code block, add callout explanations starting with the callout number
                3. Use [source] or [subs="+quotes,+macros"] blocks for code with callouts
                
                Example format:
                [source,yaml]
                ----
                hosts: webservers <1>
                  vars:
                    http_port: 8080 <2>
                ----
                <1> Targets the webservers group
                <2> Sets the HTTP port variable
                
                Important rules from Red Hat style guide:
                - Include callout numbers and callout lists to explain example files and YAML manifests
                - Do not include backslashes (\\) before callouts in the AsciiDoc output
                - Do not include "#" or "##" before the [subs=] tags
                - Display backticks with 2 plus signs: ++`++code++`++
                ==============================================
                """
                return "\n".join(style_guides) + callout_info
            return None
            
        except Exception as e:
            print(f"Warning: Could not load Red Hat style guides: {e}")
            return None
    
    def _load_rag_data(self, sona_path: Optional[str] = None) -> Optional[Dict]:
        """Load RAG data from file specified in persona config, including referenced files"""
        if not sona_path or not os.path.exists(sona_path):
            return None
        
        try:
            with open(sona_path, 'r') as f:
                sona_data = json.load(f)
            
            # Check for rag_file field in persona
            rag_file = sona_data.get("rag_file")
            if not rag_file:
                return None
            
            # Determine RAGs directory
            rags_dir = self.rags_dir
            if not rags_dir:
                # Try environment variable first
                rags_dir = os.getenv("MO11Y_RAGS_DIR")
                
                # Try to get from config
                if not rags_dir:
                    try:
                        config_path = "config.json"
                        if os.path.exists(config_path):
                            with open(config_path, "r") as f:
                                config = json.load(f)
                                rags_dir = config.get("rags_dir", "./RAGs/")
                    except:
                        rags_dir = "./RAGs/"
                
                # Expand relative paths
                if rags_dir and not os.path.isabs(rags_dir):
                    rags_dir = os.path.abspath(rags_dir)
            
            # Load main RAG file and all referenced files
            all_rag_data = {}
            self._load_rag_file_recursive(rag_file, rags_dir, all_rag_data, max_depth=3)
            
            if not all_rag_data:
                return None
            
            # If only one file, return it directly; otherwise return combined dict
            if len(all_rag_data) == 1:
                return list(all_rag_data.values())[0]
            else:
                # Combine all RAG data into a single structure
                combined = {
                    "_loaded_files": list(all_rag_data.keys()),
                    "_rag_data": all_rag_data
                }
                # Also include top-level keys from all files for easy access
                for filename, data in all_rag_data.items():
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if key not in combined:
                                combined[key] = value
                            elif isinstance(value, (list, dict)):
                                # Merge lists/dicts
                                if isinstance(combined[key], list) and isinstance(value, list):
                                    combined[key] = combined[key] + value
                                elif isinstance(combined[key], dict) and isinstance(value, dict):
                                    combined[key] = {**combined[key], **value}
                return combined
            
        except Exception as e:
            print(f"Error loading RAG data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _load_rag_file_recursive(self, rag_file: str, rags_dir: str, loaded_files: Dict, max_depth: int = 3, current_depth: int = 0):
        """Recursively load RAG file and all referenced files"""
        if current_depth >= max_depth:
            return
        
        # Normalize filename
        rag_file_normalized = rag_file
        if not rag_file_normalized.endswith('.json'):
            rag_file_normalized = f"{rag_file_normalized}.json"
        
        # Skip if already loaded
        if rag_file_normalized in loaded_files:
            return
        
        # Load the file
        rag_path = os.path.join(rags_dir, rag_file_normalized)
        if not os.path.exists(rag_path):
            # Try without .json extension
            rag_path_alt = os.path.join(rags_dir, rag_file)
            if os.path.exists(rag_path_alt):
                rag_path = rag_path_alt
            else:
                print(f"Warning: RAG file not found: {rag_path}")
                return
        
        try:
            with open(rag_path, 'r', encoding='utf-8') as f:
                rag_data = json.load(f)
            
            # Store loaded data
            loaded_files[rag_file_normalized] = rag_data
            
            # Find and load referenced RAG files
            if isinstance(rag_data, dict):
                # Check personal_data.family_members for rag_file references
                if "personal_data" in rag_data and isinstance(rag_data["personal_data"], dict):
                    family_members = rag_data["personal_data"].get("family_members", [])
                    if isinstance(family_members, list):
                        for member in family_members:
                            if isinstance(member, dict) and "rag_file" in member:
                                ref_file = member["rag_file"]
                                if ref_file and ref_file.strip():
                                    self._load_rag_file_recursive(ref_file, rags_dir, loaded_files, max_depth, current_depth + 1)
                
                # Check for rag_file references in isekai_life section
                if "isekai_life" in rag_data and isinstance(rag_data["isekai_life"], dict):
                    # Handle both single reference and list of references
                    if "rag_file_reference" in rag_data["isekai_life"]:
                        ref_file = rag_data["isekai_life"]["rag_file_reference"]
                        if ref_file and ref_file.strip():
                            self._load_rag_file_recursive(ref_file, rags_dir, loaded_files, max_depth, current_depth + 1)
                    if "rag_file_references" in rag_data["isekai_life"]:
                        ref_files = rag_data["isekai_life"]["rag_file_references"]
                        if isinstance(ref_files, list):
                            for ref_file in ref_files:
                                if ref_file and ref_file.strip():
                                    self._load_rag_file_recursive(ref_file, rags_dir, loaded_files, max_depth, current_depth + 1)
                        elif ref_files and ref_files.strip():
                            self._load_rag_file_recursive(ref_files, rags_dir, loaded_files, max_depth, current_depth + 1)
                
                # Also check for rag_file in parents/siblings arrays
                for key in ["parents", "siblings", "children"]:
                    if key in rag_data and isinstance(rag_data[key], list):
                        for item in rag_data[key]:
                            if isinstance(item, dict) and "rag_file" in item:
                                ref_file = item["rag_file"]
                                if ref_file and ref_file.strip():
                                    self._load_rag_file_recursive(ref_file, rags_dir, loaded_files, max_depth, current_depth + 1)
        
        except Exception as e:
            print(f"Error loading RAG file {rag_file_normalized}: {e}")
    
    def _get_external_api_context(self, user_input: str = None) -> str:
        """Get context from external APIs"""
        if not self.external_apis:
            return ""
        
        context_parts = []
        
        # Check if user is asking about weather
        weather_keywords = ["weather", "temperature", "forecast", "rain", "snow", 
                           "sunny", "cloudy", "hot", "cold", "humid", "wind", 
                           "tomorrow", "today", "morning", "afternoon", "evening"]
        is_weather_query = False
        location = None
        
        if user_input:
            user_input_lower = user_input.lower()
            # Check for weather-related queries (including time references)
            is_weather_query = any(keyword in user_input_lower for keyword in weather_keywords)
            
            # Try to extract location from user input
            if is_weather_query:
                words = user_input.split()
                for i, word in enumerate(words):
                    if word.lower() in ["in", "at", "for"] and i + 1 < len(words):
                        # Try to get location after "in", "at", or "for"
                        potential_location = " ".join(words[i+1:i+3]) if i+2 < len(words) else words[i+1]
                        location = potential_location.rstrip(".,!?")
                        break
                
                # If no location found, try to get default from config or use Crandall, TX
                if not location:
                    # Try to get default location from config
                    try:
                        import json
                        import os
                        config_path = "config.json"
                        if os.path.exists(config_path):
                            with open(config_path, "r") as f:
                                config = json.load(f)
                                location = config.get("default_location", "Crandall, TX")
                    except:
                        location = "Crandall, TX"  # Default location
        
        # Get weather if requested
        if is_weather_query:
            weather = self.external_apis.get_weather(location)
            if weather:
                # Detailed weather for weather queries
                context_parts.append("\nWEATHER INFORMATION (use this to answer the user's question):")
                context_parts.append(f"Location: {weather.get('location', 'Unknown')}")
                context_parts.append(f"Temperature: {weather.get('temperature', 'N/A')}°F")
                context_parts.append(f"Feels like: {weather.get('feels_like', weather.get('temperature', 'N/A'))}°F")
                context_parts.append(f"Conditions: {weather.get('description', 'N/A').title()}")
                context_parts.append(f"Humidity: {weather.get('humidity', 'N/A')}%")
                if weather.get('wind_speed'):
                    context_parts.append(f"Wind Speed: {weather.get('wind_speed', 'N/A')} mph")
                context_parts.append("\nIMPORTANT: Answer the user's weather question using this information. If they ask about 'tomorrow' or a specific time, note that this is current weather - you can mention that forecast data would be needed for future dates.")
            else:
                # Weather API not configured or failed
                context_parts.append("\nWEATHER QUERY DETECTED:")
                context_parts.append("The user is asking about weather, but weather API is not configured or unavailable.")
                context_parts.append("To enable weather: Run 'python3 setup_weather.py' to configure a weather API key.")
                context_parts.append("You should let the user know that weather information is not currently available.")
        
        return "\n".join(context_parts)
    
    def _get_local_services_context(self, user_input: str) -> tuple[str, dict]:
        """Get context from LOCAL services (calendar, reminders, tasks)
        
        Returns:
            tuple: (context_string, data_sources_dict)
        """
        context_parts = []
        data_sources = {
            "calendar_events": [],
            "reminders": [],
            "tasks": [],
            "overdue_tasks": [],
            "bills": [],
            "overdue_bills": []
        }
        
        # Get calendar events from LOCAL calendar
        from datetime import timedelta
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
        events = self.local_calendar.get_events(start_date=start_date, end_date=end_date)
        if events:
            context_parts.append("Upcoming Calendar Events (Local - ACTUAL SCHEDULED EVENTS):")
            for event in events[:5]:  # Next 5 events
                title = event.get('title', 'Event')
                start = event.get('start_time', 'Unknown')
                end = event.get('end_time', '')
                description = event.get('description', '')
                event_str = f"- {title} on {start}"
                if end:
                    event_str += f" until {end}"
                if description:
                    event_str += f" ({description})"
                context_parts.append(event_str)
                # Track for logging
                data_sources["calendar_events"].append({
                    "title": title,
                    "start_time": start,
                    "end_time": end,
                    "description": description
                })
        else:
            # Check if user is asking about calendar - if so, explicitly state no events
            calendar_keywords = ["calendar", "calendars", "upcoming", "events", "schedule", "scheduled", 
                               "what's on", "what is on", "show me my calendar", "my calendar"]
            if any(keyword in user_input.lower() for keyword in calendar_keywords):
                context_parts.append("Upcoming Calendar Events (Local):")
                context_parts.append("No upcoming calendar events found in the next 7 days.")
                context_parts.append("(Note: Journal entries are HISTORICAL events, not current calendar events)")
        
        # Get pending reminders from LOCAL reminder service
        reminders = self.reminder_service.get_pending_reminders()
        if reminders:
            context_parts.append("\nPending Reminders:")
            for reminder in reminders[:5]:  # Next 5 reminders
                title = reminder.get('title', 'Reminder')
                reminder_time = reminder.get('reminder_time', 'Unknown')
                context_parts.append(f"- {title} (due: {reminder_time})")
                # Track for logging
                data_sources["reminders"].append({
                    "title": title,
                    "reminder_time": reminder_time
                })
        
        # Get pending tasks from LOCAL task service
        tasks = self.task_service.get_pending_tasks()
        if tasks:
            context_parts.append("\nPending Tasks:")
            for task in tasks[:5]:  # Next 5 tasks
                title = task.get('title', 'Task')
                priority = task.get('priority', 'medium')
                importance = task.get('importance', 5)
                due_date = task.get('due_date', '')
                due_str = f" (due: {due_date})" if due_date else ""
                context_parts.append(f"- [{priority.upper()}] Importance: {importance}/10 - {title}{due_str}")
                # Track for logging
                data_sources["tasks"].append({
                    "title": title,
                    "priority": priority,
                    "importance": importance,
                    "due_date": due_date
                })
        
        # Get overdue tasks
        overdue_tasks = self.task_service.get_overdue_tasks()
        if overdue_tasks:
            context_parts.append("\n⚠️ Overdue Tasks:")
            for task in overdue_tasks[:3]:  # Next 3 overdue
                title = task.get('title', 'Task')
                importance = task.get('importance', 5)
                due_date = task.get('due_date', 'Unknown')
                context_parts.append(f"- Importance: {importance}/10 - {title} (was due: {due_date})")
                # Track for logging
                data_sources["overdue_tasks"].append({
                    "title": title,
                    "importance": importance,
                    "due_date": due_date
                })
        
        # Get upcoming bills from LOCAL financial service
        upcoming_bills = self.financial_service.get_upcoming_bills(days_ahead=30)
        if upcoming_bills:
            context_parts.append("\n💰 Upcoming Bills:")
            total_due = 0
            for bill in upcoming_bills[:5]:  # Next 5 bills
                name = bill.get('name', 'Bill')
                amount = bill.get('amount', 0)
                importance = bill.get('importance', 5)
                due_date = bill.get('due_date', 'Unknown')
                category = bill.get('category', '')
                category_str = f" [{category}]" if category else ""
                context_parts.append(f"- Importance: {importance}/10 - {name}{category_str}: ${amount:.2f} (due: {due_date})")
                total_due += amount
                # Track for logging
                data_sources["bills"].append({
                    "name": name,
                    "amount": amount,
                    "importance": importance,
                    "due_date": due_date,
                    "category": category
                })
            if len(upcoming_bills) > 5:
                context_parts.append(f"  ... and {len(upcoming_bills) - 5} more bills")
            context_parts.append(f"  Total due in next 30 days: ${total_due:.2f}")
        
        # Get overdue bills
        overdue_bills = self.financial_service.get_overdue_bills()
        if overdue_bills:
            context_parts.append("\n⚠️ Overdue Bills:")
            overdue_total = 0
            for bill in overdue_bills[:3]:  # Next 3 overdue
                name = bill.get('name', 'Bill')
                amount = bill.get('amount', 0)
                importance = bill.get('importance', 5)
                due_date = bill.get('due_date', 'Unknown')
                context_parts.append(f"- Importance: {importance}/10 - {name}: ${amount:.2f} (was due: {due_date})")
                overdue_total += amount
                # Track for logging
                data_sources["overdue_bills"].append({
                    "name": name,
                    "amount": amount,
                    "importance": importance,
                    "due_date": due_date
                })
            context_parts.append(f"  Total overdue: ${overdue_total:.2f}")
        
        return ("\n".join(context_parts) if context_parts else "", data_sources)
    
    def handle_calendar_actions(self, user_input: str) -> Optional[str]:
        """Detect and handle calendar add/delete actions using LOCAL calendar"""
        user_input_lower = user_input.lower()
        
        # Detect add event
        add_keywords = ["add", "create", "schedule", "set up", "book"]
        if any(keyword in user_input_lower for keyword in add_keywords):
            context_parts = []
            context_parts.append("\nLOCAL CALENDAR ACTION AVAILABLE:")
            context_parts.append("You can add calendar events using: self.local_calendar.add_event()")
            context_parts.append("Parameters: title (str), start_time (datetime), end_time (datetime, optional), description (str, optional)")
            context_parts.append("Example: self.local_calendar.add_event('Meeting', datetime(2025, 12, 30, 14, 0), datetime(2025, 12, 30, 15, 0), 'Team meeting')")
            return "\n".join(context_parts)
        
        # Detect delete event
        delete_keywords = ["delete", "remove", "cancel", "clear"]
        if any(keyword in user_input_lower for keyword in delete_keywords):
            context_parts = []
            context_parts.append("\nLOCAL CALENDAR ACTION AVAILABLE:")
            context_parts.append("Note: Calendar events can be deleted by ID. List events first to get IDs.")
            return "\n".join(context_parts)
        
        return None
    
    def handle_reminder_actions(self, user_input: str) -> Optional[str]:
        """Detect and handle reminder actions using LOCAL reminder service"""
        user_input_lower = user_input.lower()
        
        # Detect add reminder
        reminder_keywords = ["remind", "reminder", "set reminder", "create reminder"]
        if any(keyword in user_input_lower for keyword in reminder_keywords):
            context_parts = []
            context_parts.append("\nLOCAL REMINDER ACTION AVAILABLE:")
            context_parts.append("You can add reminders using: self.reminder_service.add_reminder()")
            context_parts.append("Parameters: title (str), reminder_time (datetime), description (str, optional)")
            context_parts.append("Example: self.reminder_service.add_reminder('Call mom', datetime(2025, 12, 30, 18, 0), 'Call to check in')")
            return "\n".join(context_parts)
        
        return None
    
    def handle_task_actions(self, user_input: str) -> Optional[str]:
        """Detect and handle task actions using LOCAL task service"""
        user_input_lower = user_input.lower()
        
        # Detect task-related keywords
        task_keywords = ["task", "todo", "to-do", "add task", "create task", "complete task"]
        if any(keyword in user_input_lower for keyword in task_keywords):
            context_parts = []
            context_parts.append("\nLOCAL TASK ACTION AVAILABLE:")
            context_parts.append("You can manage tasks using:")
            context_parts.append("- Add: self.task_service.add_task(title, description, due_date, priority)")
            context_parts.append("- Complete: self.task_service.mark_completed(task_id)")
            context_parts.append("- List: self.task_service.get_pending_tasks()")
            context_parts.append("Priority options: 'high', 'medium', 'low'")
            context_parts.append("Example: self.task_service.add_task('Finish report', 'Write quarterly report', datetime(2025, 12, 31), 'high')")
            return "\n".join(context_parts)
        
        return None
    
    def handle_financial_actions(self, user_input: str) -> Optional[str]:
        """Detect and handle financial/bill actions using LOCAL financial service"""
        user_input_lower = user_input.lower()
        
        # Detect bill-related keywords
        bill_keywords = ["bill", "bills", "payment", "payments", "due", "owe", "financial"]
        add_keywords = ["add", "create", "new", "set", "update", "change"]
        
        has_bill_keyword = any(keyword in user_input_lower for keyword in bill_keywords)
        has_add_keyword = any(keyword in user_input_lower for keyword in add_keywords)
        
        if has_bill_keyword and has_add_keyword:
            context_parts = []
            context_parts.append("\nLOCAL FINANCIAL ACTION AVAILABLE:")
            context_parts.append("You can manage bills using:")
            context_parts.append("- Add bill: self.financial_service.add_bill(name, amount, due_date, frequency='monthly', importance=5, category=None)")
            context_parts.append("- Update bill: self.financial_service.update_bill(bill_id, name=None, amount=None, due_date=None, importance=None)")
            context_parts.append("- Mark paid: self.financial_service.mark_bill_paid(bill_id, paid_date=None, amount_paid=None)")
            context_parts.append("- List bills: self.financial_service.get_upcoming_bills(days_ahead=30)")
            context_parts.append("Importance: 1-10 scale (10 = critical, 1 = low)")
            context_parts.append("Frequency: 'monthly', 'quarterly', 'yearly', 'one-time'")
            context_parts.append("Example: self.financial_service.add_bill('Electric Bill', 125.50, datetime(2026, 1, 7), 'monthly', importance=9, category='utilities')")
            return "\n".join(context_parts)
        
        return None
    
    def execute_mcp_tool(self, tool_name: str, arguments: Dict, context: Dict = None) -> Dict:
        """Execute an MCP tool"""
        if not self.mcp_executor:
            return {"success": False, "error": "MCP not enabled"}
        
        return self.mcp_executor.execute_tool(tool_name, arguments, context)
    
    def chat(self, user_input: str, config: Optional[Dict] = None, thread_id: str = "default") -> Dict:
        """Main chat interface"""
        # Extract media from config if provided
        media_files = []
        if config and config.get("media_files"):
            media_files = config["media_files"]
        
        # Initialize state
        initial_state = {
            "user_input": user_input,
            "messages": [],
            "user_sentiment": 0.0,
            "context": {},
            "memories_retrieved": {},
            "personality_context": "",
            "response": "",
            "should_proact": False,
            "proactivity_suggestions": [],
            "interaction_metadata": {
                "media_files": media_files
            }
        }
        
        # Run graph if available, otherwise run sequentially
        if self.graph is not None:
            # LangGraph requires configurable keys (thread_id) when using checkpointer
            graph_config = config or {}
            if "configurable" not in graph_config:
                graph_config["configurable"] = {}
            if "thread_id" not in graph_config["configurable"]:
                graph_config["configurable"]["thread_id"] = thread_id
            
            result = self.graph.invoke(initial_state, graph_config)
        else:
            # Fallback: run nodes sequentially
            state = initial_state
            state = self.analyze_input(state)
            state = self.retrieve_memories(state)
            state = self.get_personality_context(state)
            state = self.generate_response(state)
            state = self.store_memory(state)
            state = self.adapt_personality(state)
            state = self.check_proactivity(state)
            result = state
        
        # Log the conversation exchange
        if self.logger:
            # Get metadata
            metadata = {
                "model": self.model_name,
                "persona": os.path.basename(self.sona_path) if self.sona_path else "default",
                "thread_id": thread_id
            }
            
            # Set data sources used for logging
            data_sources = result.get("data_sources", {})
            if data_sources.get("rag_files"):
                self.logger.set_rag_used(data_sources["rag_files"])
            if data_sources.get("journal_entries"):
                self.logger.set_journal_used(data_sources["journal_entries"])
            if data_sources.get("mcp_tools"):
                self.logger.set_mcp_tools_used(data_sources["mcp_tools"])
            
            # Log the exchange with full state
            self.logger.log_exchange(
                user_input=user_input,
                agent_response=result.get("response", ""),
                state=result,
                metadata=metadata
            )
        
        # Update persona JSON after conversation (if updater available)
        if self.sona_path:
            sona_lower = self.sona_path.lower()
            
            # Extract information from conversation (shared for both personas)
            context = result.get("context", {})
            topics_discussed = context.get("topics", [])
            sentiment_score = result.get("user_sentiment", 0.0)
            agent_response = result.get("response", "")
            
            # Extract new information learned (simplified - could be enhanced with LLM)
            new_info = []
            user_lower = user_input.lower()
            if any(word in user_lower for word in ["i'm", "i am", "i work", "i have", "i feel", "i was", "i did"]):
                sentences = user_input.split('.')
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(word in sentence_lower for word in ["i'm", "i am", "i work", "i have", "i feel", "i was", "i did"]):
                        new_info.append(sentence.strip()[:200])
            
            # Extract follow-up topics (questions or unresolved statements)
            followup_topics = []
            if "?" in user_input:
                sentences = user_input.split('?')
                for sentence in sentences:
                    if sentence.strip() and len(sentence.strip()) > 10:
                        followup_topics.append(sentence.strip()[:150])
            if any(phrase in user_lower for phrase in ["i'll tell you later", "remind me", "we should talk about", "i need to"]):
                followup_topics.append("Topic mentioned but not fully discussed")
            
            # Note: Emotional moment tracking removed - this is a business tool
            emotional_moments = []
            
            # Update CJS JSON after conversation (if CJS persona)
            if CJS_UPDATER_AVAILABLE and ("cjs" in sona_lower or "carroll" in sona_lower):
                try:
                    updater = CJSConversationUpdater(cjs_json_path=self.sona_path)
                    
                    # Check for isekai stories in response
                    isekai_stories = []
                    if any(word in agent_response.lower() for word in ["quest", "dungeon", "guild", "adventure", "rank", "isekai"]):
                        sentences = agent_response.split('.')
                        for sentence in sentences:
                            if any(word in sentence.lower() for word in ["quest", "dungeon", "guild", "adventure", "rank"]):
                                isekai_stories.append(sentence.strip())
                    
                    # Check if user is asking about quests/adventures and generate if needed
                    quest_keywords = ["what quest", "what adventure", "tell me about your quest", "what are you working on", "any new quest"]
                    is_quest_query = any(keyword in user_lower for keyword in quest_keywords)
                    
                    # Generate quest if asked and no active quests
                    if QUEST_SYSTEM_AVAILABLE and is_quest_query:
                        try:
                            quest_system = JimQuestSystem(cjs_json_path=self.sona_path)
                            active_quests = quest_system.get_active_quests()
                            if not active_quests:
                                new_quest = quest_system.generate_quest(rank="E")
                                quest_system.add_quest(new_quest)
                        except Exception as e:
                            pass
                    
                    # Update CJS JSON
                    updater.update_after_conversation(
                        user_input=user_input,
                        agent_response=agent_response,
                        conversation_summary=None,
                        new_information_learned=new_info if new_info else None,
                        topics_needing_followup=followup_topics if followup_topics else None,
                        isekai_stories_shared=isekai_stories if isekai_stories else None,
                        sentiment_score=sentiment_score,
                        topics_discussed=topics_discussed
                    )
                except Exception as e:
                    print(f"Warning: Failed to update CJS JSON: {e}")
            
            # Update Alex JSON after conversation (if Alex persona)
            elif ALEX_UPDATER_AVAILABLE and "alex" in sona_lower:
                try:
                    updater = AlexConversationUpdater(alex_json_path=self.sona_path)
                    
                    # Update Alex JSON
                    updater.update_after_conversation(
                        user_input=user_input,
                        agent_response=agent_response,
                        conversation_summary=None,
                        new_information_learned=new_info if new_info else None,
                        topics_needing_followup=followup_topics if followup_topics else None,
                        sentiment_score=sentiment_score,
                        topics_discussed=topics_discussed
                    )
                except Exception as e:
                    print(f"Warning: Failed to update Alex JSON: {e}")
        
        return {
            "response": result.get("response", ""),
            "memories_used": len(result.get("memories_retrieved", {}).get("episodic", [])),
            "should_proact": result.get("should_proact", False),
            "proactivity_suggestions": result.get("proactivity_suggestions", []),
            "log_file": self.logger.get_log_file_path() if self.logger else None
        }


# Convenience function for easy usage
def create_mo11y_agent(model_name: str = "deepseek-r1:latest",
                       db_path: str = "mo11y_companion.db",
                       sona_path: Optional[str] = None,
                       enable_mcp: bool = True,
                       enable_external_apis: bool = True,
                       suppress_thinking: bool = True,
                       rags_dir: Optional[str] = None,
                       enable_logging: bool = True) -> Mo11yAgent:
    """Create and return a Mo11y agent instance"""
    return Mo11yAgent(
        model_name=model_name,
        db_path=db_path,
        sona_path=sona_path,
        enable_mcp=enable_mcp,
        enable_external_apis=enable_external_apis,
        suppress_thinking=suppress_thinking,
        rags_dir=rags_dir,
        enable_logging=enable_logging
    )
