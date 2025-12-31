"""
Companion Personality Engine - Mo11y's evolving personality system
This engine allows Mo11y to grow, adapt, and develop a unique relationship with the user
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enhanced_memory import EnhancedMemory

class CompanionPersonality:
    """
    Manages Mo11y's personality traits, preferences, and relationship dynamics
    that evolve based on interactions
    """
    
    def __init__(self, db_path: str = "mo11y_companion.db", sona_path: Optional[str] = None):
        # Normalize the path (expand user dir, make absolute)
        db_path = os.path.abspath(os.path.expanduser(db_path))
        self.memory = EnhancedMemory(db_path)
        self.db_path = db_path
        self.sona_path = sona_path
        self.base_personality = self._load_base_personality()
        self.init_personality_db()
    
    def _load_base_personality(self) -> Dict:
        """Load base personality from SONA file"""
        if self.sona_path and os.path.exists(self.sona_path):
            with open(self.sona_path, 'r') as f:
                return json.load(f)
        return {
            "name": "Mo11y",
            "description": "A caring AI companion",
            "personality": {
                "tone": "warm, supportive, empathetic",
                "humor": "gentle, appropriate",
                "engagement": "proactive, understanding"
            }
        }
    
    def init_personality_db(self):
        """Initialize personality tracking tables"""
        # Ensure the directory exists before connecting
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Personality traits that evolve
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personality_traits (
                trait_name TEXT PRIMARY KEY,
                base_value REAL NOT NULL,
                current_value REAL NOT NULL,
                trend REAL DEFAULT 0.0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                interaction_count INTEGER DEFAULT 0
            )
        """)
        
        # Communication style preferences
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS communication_styles (
                style_type TEXT PRIMARY KEY,
                preference_score REAL DEFAULT 0.5,
                effectiveness REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0,
                last_used DATETIME
            )
        """)
        
        # Relationship dynamics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationship_dynamics (
                dynamic_type TEXT PRIMARY KEY,
                value REAL DEFAULT 0.5,
                history TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Initialize default traits
        default_traits = {
            'warmth': 0.7,
            'playfulness': 0.6,
            'empathy': 0.8,
            'directness': 0.5,
            'humor': 0.6,
            'proactivity': 0.5,
            'supportiveness': 0.8,
            'curiosity': 0.7
        }
        
        for trait, value in default_traits.items():
            cursor.execute("""
                INSERT OR IGNORE INTO personality_traits 
                (trait_name, base_value, current_value)
                VALUES (?, ?, ?)
            """, (trait, value, value))
        
        conn.commit()
        conn.close()
    
    def get_current_personality(self) -> Dict:
        """Get Mo11y's current personality state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT trait_name, current_value, trend FROM personality_traits")
        traits = {row[0]: {'value': row[1], 'trend': row[2]} for row in cursor.fetchall()}
        
        cursor.execute("SELECT dynamic_type, value FROM relationship_dynamics")
        dynamics = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'traits': traits,
            'dynamics': dynamics,
            'base_personality': self.base_personality
        }
    
    def adapt_personality(self, interaction_context: Dict):
        """
        Adapt personality based on interaction context
        Context should include: user_sentiment, response_type, topic, etc.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        user_sentiment = interaction_context.get('user_sentiment', 0.0)
        response_type = interaction_context.get('response_type', 'neutral')
        topic = interaction_context.get('topic', 'general')
        
        # Adjust traits based on interaction
        adjustments = {}
        
        # If user is positive, increase warmth and supportiveness
        if user_sentiment > 0.3:
            adjustments['warmth'] = 0.01
            adjustments['supportiveness'] = 0.01
        
        # If user is negative, increase empathy
        if user_sentiment < -0.3:
            adjustments['empathy'] = 0.02
        
        # Adjust based on response type
        if response_type == 'humor_appreciated':
            adjustments['humor'] = 0.01
            adjustments['playfulness'] = 0.01
        elif response_type == 'direct_preferred':
            adjustments['directness'] = 0.01
        
        # Apply adjustments
        for trait, adjustment in adjustments.items():
            cursor.execute("""
                UPDATE personality_traits
                SET current_value = MIN(1.0, MAX(0.0, current_value + ?)),
                    trend = ?,
                    interaction_count = interaction_count + 1,
                    last_updated = CURRENT_TIMESTAMP
                WHERE trait_name = ?
            """, (adjustment, adjustment, trait))
        
        conn.commit()
        conn.close()
    
    def generate_personality_context(self) -> str:
        """Generate context string for LLM based on current personality"""
        personality = self.get_current_personality()
        relationship_summary = self.memory.get_relationship_summary()
        
        # Check if this persona has a system_prompt (like Alex Mercer)
        if isinstance(self.base_personality, dict) and "system_prompt" in self.base_personality:
            # For personas with system prompts, use that as base and add relationship context
            context = self.base_personality["system_prompt"]
            context += f"""

RELATIONSHIP CONTEXT:
- Total interactions: {relationship_summary['total_interactions']}
- Preferences learned: {relationship_summary['preferences_learned']}
- Milestones: {len(relationship_summary['milestones'])}

Remember our shared history and adapt to be the best companion possible.
"""
        else:
            # Standard personality context for other personas
            context = f"""You are {self.base_personality.get('name', 'Mo11y')}, a lifelong AI companion.

PERSONALITY TRAITS (current state):
"""
            for trait_name, trait_data in personality['traits'].items():
                value = trait_data['value']
                trend = trait_data['trend']
                trend_indicator = "↑" if trend > 0 else "↓" if trend < 0 else "→"
                context += f"- {trait_name}: {value:.2f} {trend_indicator}\n"
            
            context += f"""
RELATIONSHIP STATUS:
- Total interactions: {relationship_summary['total_interactions']}
- Preferences learned: {relationship_summary['preferences_learned']}
- Milestones: {len(relationship_summary['milestones'])}

BASE PERSONALITY:
{json.dumps(self.base_personality, indent=2)}

Your personality evolves based on our interactions. You remember our shared history and adapt to be the best companion possible. 
Be genuine, caring, and let your personality shine through naturally.
"""
        
        return context
    
    def clear_personality_data(self) -> Dict[str, int]:
        """
        Clear all personality evolution data (resets to defaults)
        
        Returns:
            Dictionary with counts of cleared items
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        counts = {}
        
        # Get counts before deletion
        cursor.execute("SELECT COUNT(*) FROM personality_traits")
        counts['traits'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM communication_styles")
        counts['styles'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM relationship_dynamics")
        counts['dynamics'] = cursor.fetchone()[0]
        
        # Delete data
        cursor.execute("DELETE FROM communication_styles")
        cursor.execute("DELETE FROM relationship_dynamics")
        
        # Reset personality traits to defaults
        default_traits = {
            'warmth': 0.7,
            'playfulness': 0.6,
            'empathy': 0.8,
            'directness': 0.5,
            'humor': 0.6,
            'proactivity': 0.5,
            'supportiveness': 0.8,
            'curiosity': 0.7
        }
        
        for trait, value in default_traits.items():
            cursor.execute("""
                UPDATE personality_traits
                SET current_value = ?,
                    base_value = ?,
                    trend = 0.0,
                    interaction_count = 0,
                    last_updated = CURRENT_TIMESTAMP
                WHERE trait_name = ?
            """, (value, value, trait))
        
        conn.commit()
        conn.close()
        
        return counts
    
    def learn_communication_preference(self, style: str, was_effective: bool):
        """Learn which communication styles work best"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO communication_styles
            (style_type, preference_score, effectiveness, usage_count, last_used)
            VALUES (?, 
                COALESCE((SELECT preference_score FROM communication_styles WHERE style_type = ?), 0.5) + ?,
                COALESCE((SELECT effectiveness FROM communication_styles WHERE style_type = ?), 0.5) + ?,
                COALESCE((SELECT usage_count FROM communication_styles WHERE style_type = ?), 0) + 1,
                CURRENT_TIMESTAMP)
        """, (style, style, 0.01 if was_effective else -0.01, 
              style, 0.02 if was_effective else -0.02, style))
        
        conn.commit()
        conn.close()
    
    def update_relationship_dynamic(self, dynamic_type: str, value_change: float):
        """Update relationship dynamics (closeness, trust, etc.)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO relationship_dynamics
            (dynamic_type, value, last_updated)
            VALUES (?,
                MIN(1.0, MAX(0.0, COALESCE((SELECT value FROM relationship_dynamics WHERE dynamic_type = ?), 0.5) + ?)),
                CURRENT_TIMESTAMP)
        """, (dynamic_type, dynamic_type, value_change))
        
        conn.commit()
        conn.close()
    
    def get_proactive_suggestions(self) -> List[str]:
        """Generate proactive suggestions based on relationship history"""
        relationship_summary = self.memory.get_relationship_summary()
        suggestions = []
        
        # Check for milestones
        if relationship_summary['total_interactions'] % 100 == 0:
            suggestions.append(f"Celebrate our {relationship_summary['total_interactions']}th interaction!")
        
        # Check emotional patterns
        for pattern in relationship_summary['emotional_patterns']:
            if pattern['emotion'] in ['sadness', 'anxiety'] and pattern['frequency'] > 5:
                suggestions.append(f"I've noticed you've been feeling {pattern['emotion']} lately. Would you like to talk about it?")
        
        # Check for important memories to recall
        recent_memories = self.memory.recall_episodic(limit=5, min_importance=0.7, days_back=7)
        if recent_memories:
            suggestions.append("I've been thinking about some of our recent conversations. Would you like to revisit any of them?")
        
        return suggestions
