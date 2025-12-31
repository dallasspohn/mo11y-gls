"""
Server-Based Agent - For remote Ollama deployment
Handles connection to remote Ollama server with better error handling
"""

import os
import requests
from typing import Dict, Optional, List
from mo11y_agent import Mo11yAgent, AgentState
from enhanced_memory import EnhancedMemory
from companion_engine import CompanionPersonality
from life_journal import LifeJournal


class ServerMo11yAgent(Mo11yAgent):
    """
    Server-based version of Mo11yAgent
    Connects to remote Ollama server with retry logic and better error handling
    """
    
    def __init__(self, 
                 model_name: str = "deepseek-r1:latest",
                 db_path: str = "mo11y_companion.db",
                 sona_path: Optional[str] = None,
                 ollama_host: Optional[str] = None,
                 ollama_port: int = 11434,
                 max_retries: int = 3):
        """
        Initialize server-based agent
        
        Args:
            model_name: Model to use
            db_path: Database path
            sona_path: Persona file path
            ollama_host: Ollama server host (default: from env or localhost)
            ollama_port: Ollama server port
            max_retries: Maximum retry attempts
        """
        # Set Ollama host before initializing parent
        self.ollama_host = ollama_host or os.getenv("OLLAMA_HOST", "http://localhost")
        self.ollama_port = ollama_port
        self.ollama_base_url = f"{self.ollama_host}:{self.ollama_port}"
        self.max_retries = max_retries
        
        # Set environment variable for ollama client
        os.environ["OLLAMA_HOST"] = self.ollama_base_url
        
        # Initialize parent
        super().__init__(model_name, db_path, sona_path)
    
    def _check_ollama_connection(self) -> bool:
        """Check if Ollama server is accessible"""
        try:
            response = requests.get(
                f"{self.ollama_base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def generate_response(self, state: AgentState) -> AgentState:
        """Generate response with server connection handling"""
        # Check connection first
        if not self._check_ollama_connection():
            state["response"] = (
                "I'm unable to connect to the Ollama server. "
                "Please ensure the server is running and accessible. "
                f"Trying to connect to: {self.ollama_base_url}"
            )
            return state
        
        # Use parent's generate_response with retry logic
        return self._generate_with_retry(state)
    
    def _generate_with_retry(self, state: AgentState) -> AgentState:
        """Generate response with retry logic"""
        user_input = state.get("user_input", "")
        memories = state.get("memories_retrieved", {})
        personality_context = state.get("personality_context", "")
        user_sentiment = state.get("user_sentiment", 0.0)
        
        # Build context (same as parent)
        system_prompt = None
        if hasattr(self.personality, 'base_personality') and isinstance(self.personality.base_personality, dict):
            system_prompt = self.personality.base_personality.get("system_prompt")
        
        context_parts = []
        
        if system_prompt:
            context_parts.append(system_prompt)
            context_parts.append("\n\nCONTEXT FROM OUR RELATIONSHIP:")
        else:
            context_parts.append(personality_context)
        
        # Add episodic memories
        if memories.get("episodic"):
            context_parts.append("\nRELEVANT MEMORIES:")
            for mem in memories["episodic"][:3]:
                context_parts.append(f"- [{mem['timestamp']}] {mem['content']}")
        
        # Add semantic memories
        if memories.get("semantic"):
            context_parts.append("\nRELEVANT KNOWLEDGE:")
            for key, value in memories["semantic"].items():
                if isinstance(value, dict):
                    context_parts.append(f"- {key}: {value.get('value', '')}")
        
        # Add life journal context if available
        if self.life_journal:
            journal_summary = self.life_journal.get_summary()
            context_parts.append(f"\nLIFE JOURNAL CONTEXT:\n{journal_summary}")
        
        # Add conversation history
        if state.get("messages"):
            context_parts.append("\nRECENT CONVERSATION:")
            for msg in state["messages"][-4:]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                context_parts.append(f"{role}: {content}")
        
        full_context = "\n".join(context_parts)
        full_prompt = f"{full_context}\n\nUser: {user_input}\nAssistant:"
        
        # Generate response with retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                from ollama import chat
                
                stream = chat(
                    model=self.model_name,
                    messages=[{"role": "system", "content": full_prompt}],
                    stream=True,
                )
                
                response = ""
                for chunk in stream:
                    response += chunk["message"]["content"]
                
                state["response"] = response
                
                # Add to messages
                if "messages" not in state:
                    state["messages"] = []
                state["messages"].append({"role": "user", "content": user_input})
                state["messages"].append({"role": "assistant", "content": response})
                
                return state
                
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # Wait before retry (exponential backoff)
                    import time
                    time.sleep(2 ** attempt)
                else:
                    # Final attempt failed
                    state["response"] = (
                        f"I encountered a connection error after {self.max_retries} attempts. "
                        f"Error: {str(last_error)}. "
                        f"Please check that Ollama is running at {self.ollama_base_url}"
                    )
        
        return state


def create_server_agent(model_name: str = "deepseek-r1:latest",
                        db_path: str = "mo11y_companion.db",
                        sona_path: Optional[str] = None,
                        ollama_host: Optional[str] = None,
                        ollama_port: int = 11434) -> ServerMo11yAgent:
    """Create server-based agent instance"""
    return ServerMo11yAgent(
        model_name=model_name,
        db_path=db_path,
        sona_path=sona_path,
        ollama_host=ollama_host,
        ollama_port=ollama_port
    )
