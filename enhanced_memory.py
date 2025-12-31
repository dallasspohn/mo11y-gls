"""
Enhanced Memory System for Mo11y - A Lifelong Companion
This system implements multiple memory types to create a rich, evolving relationship
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib

class EnhancedMemory:
    """
    A sophisticated memory system that tracks:
    - Episodic memories (specific events and conversations)
    - Semantic memories (facts, preferences, knowledge about the user)
    - Emotional memories (sentiment, emotional context)
    - Relationship memories (milestones, shared experiences)
    - Procedural memories (learned patterns, habits)
    """
    
    def __init__(self, db_path: str = "mo11y_companion.db"):
        # Normalize the path (expand user dir, make absolute)
        self.db_path = os.path.abspath(os.path.expanduser(db_path))
        self.init_database()
        
    def init_database(self):
        """Initialize the enhanced memory database schema"""
        # Ensure the directory exists before connecting
        db_dir = os.path.dirname(self.db_path)
        
        # Ensure the directory exists
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
            except OSError as e:
                raise OSError(f"Cannot create database directory '{db_dir}': {e}")
        
        # Verify directory is writable
        if not os.access(db_dir, os.W_OK):
            raise PermissionError(f"Database directory '{db_dir}' is not writable")
        
        try:
            conn = sqlite3.connect(self.db_path)
        except sqlite3.OperationalError as e:
            raise sqlite3.OperationalError(
                f"Cannot open database file '{self.db_path}': {e}. "
                f"Directory exists: {os.path.exists(db_dir)}, "
                f"Directory writable: {os.access(db_dir, os.W_OK) if os.path.exists(db_dir) else 'N/A'}"
            )
        cursor = conn.cursor()
        
        # Episodic memories - specific events/conversations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodic_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                content TEXT NOT NULL,
                context TEXT,
                importance_score REAL DEFAULT 0.5,
                emotional_valence REAL DEFAULT 0.0,
                emotional_arousal REAL DEFAULT 0.0,
                tags TEXT,
                relationship_context TEXT,
                consolidated BOOLEAN DEFAULT 0
            )
        """)
        
        # Semantic memories - facts and knowledge
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS semantic_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                source_memory_id INTEGER,
                last_accessed DATETIME,
                access_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_memory_id) REFERENCES episodic_memories(id)
            )
        """)
        
        # Emotional memories - sentiment tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emotional_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                emotion_type TEXT NOT NULL,
                intensity REAL NOT NULL,
                context TEXT,
                trigger TEXT,
                memory_id INTEGER,
                FOREIGN KEY (memory_id) REFERENCES episodic_memories(id)
            )
        """)
        
        # Relationship milestones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationship_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                milestone_type TEXT NOT NULL,
                description TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                significance REAL DEFAULT 0.5,
                associated_memories TEXT
            )
        """)
        
        # User preferences and patterns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                category TEXT NOT NULL,
                preference_key TEXT NOT NULL,
                preference_value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (category, preference_key)
            )
        """)
        
        # Conversation patterns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                effectiveness_score REAL DEFAULT 0.5
            )
        """)
        
        # Memory associations (for linking related memories)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_associations (
                memory_id_1 INTEGER NOT NULL,
                memory_id_2 INTEGER NOT NULL,
                association_strength REAL DEFAULT 0.5,
                association_type TEXT,
                FOREIGN KEY (memory_id_1) REFERENCES episodic_memories(id),
                FOREIGN KEY (memory_id_2) REFERENCES episodic_memories(id),
                PRIMARY KEY (memory_id_1, memory_id_2)
            )
        """)
        
        # Multi-modal media storage (images, audio, video)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS media_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER NOT NULL,
                media_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT,
                file_size INTEGER,
                mime_type TEXT,
                description TEXT,
                transcription TEXT,
                metadata TEXT,
                thumbnail_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES episodic_memories(id)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_memory_id ON media_memories(memory_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_type ON media_memories(media_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodic_timestamp ON episodic_memories(timestamp)")
        
        conn.commit()
        conn.close()
        
        # Create media storage directory
        self.media_dir = os.path.join(os.path.dirname(self.db_path), "media")
        os.makedirs(self.media_dir, exist_ok=True)
        os.makedirs(os.path.join(self.media_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(self.media_dir, "audio"), exist_ok=True)
        os.makedirs(os.path.join(self.media_dir, "thumbnails"), exist_ok=True)
    
    def remember_episodic(self, content: str, context: str = "", 
                         importance: float = 0.5, emotional_valence: float = 0.0,
                         emotional_arousal: float = 0.0, tags: List[str] = None,
                         relationship_context: str = "") -> int:
        """Store an episodic memory (specific event/conversation)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tags_str = json.dumps(tags) if tags else None
        
        cursor.execute("""
            INSERT INTO episodic_memories 
            (content, context, importance_score, emotional_valence, emotional_arousal, tags, relationship_context)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (content, context, importance, emotional_valence, emotional_arousal, tags_str, relationship_context))
        
        memory_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return memory_id
    
    def remember_semantic(self, key: str, value: str, confidence: float = 1.0,
                         source_memory_id: Optional[int] = None):
        """Store a semantic memory (fact/knowledge)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO semantic_memories 
            (key, value, confidence, source_memory_id, last_accessed, access_count)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 
                COALESCE((SELECT access_count FROM semantic_memories WHERE key = ?), 0) + 1)
        """, (key, value, confidence, source_memory_id, key))
        
        conn.commit()
        conn.close()
    
    def remember_emotion(self, emotion_type: str, intensity: float, 
                        context: str = "", trigger: str = "",
                        memory_id: Optional[int] = None):
        """Store an emotional memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO emotional_memories 
            (emotion_type, intensity, context, trigger, memory_id)
            VALUES (?, ?, ?, ?, ?)
        """, (emotion_type, intensity, context, trigger, memory_id))
        
        conn.commit()
        conn.close()
    
    def add_milestone(self, milestone_type: str, description: str, 
                     significance: float = 0.5, associated_memories: List[int] = None):
        """Record a relationship milestone"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        memories_str = json.dumps(associated_memories) if associated_memories else None
        
        cursor.execute("""
            INSERT INTO relationship_milestones 
            (milestone_type, description, significance, associated_memories)
            VALUES (?, ?, ?, ?)
        """, (milestone_type, description, significance, memories_str))
        
        conn.commit()
        conn.close()
    
    def update_preference(self, category: str, key: str, value: str, confidence: float = 1.0):
        """Update or create a user preference"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_preferences 
            (category, preference_key, preference_value, confidence, last_updated)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (category, key, value, confidence))
        
        conn.commit()
        conn.close()
    
    def get_preference(self, category: str, key: str) -> Optional[Dict]:
        """Retrieve a specific preference by category and key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT preference_key, preference_value, confidence, last_updated
            FROM user_preferences 
            WHERE category = ? AND preference_key = ?
        """, (category, key))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'key': result[0],
                'value': result[1],
                'confidence': result[2],
                'last_updated': result[3]
            }
        return None
    
    def get_preferences_by_category(self, category: str) -> Dict[str, Dict]:
        """Retrieve all preferences in a specific category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT preference_key, preference_value, confidence, last_updated
            FROM user_preferences 
            WHERE category = ?
            ORDER BY last_updated DESC
        """, (category,))
        
        results = cursor.fetchall()
        conn.close()
        
        preferences = {}
        for row in results:
            preferences[row[0]] = {
                'value': row[1],
                'confidence': row[2],
                'last_updated': row[3]
            }
        
        return preferences
    
    def get_all_preferences(self) -> Dict[str, Dict[str, Dict]]:
        """Retrieve all preferences organized by category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT category, preference_key, preference_value, confidence, last_updated
            FROM user_preferences 
            ORDER BY category, last_updated DESC
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        preferences = {}
        for row in results:
            category, key, value, confidence, last_updated = row
            if category not in preferences:
                preferences[category] = {}
            preferences[category][key] = {
                'value': value,
                'confidence': confidence,
                'last_updated': last_updated
            }
        
        return preferences
    
    def recall_episodic(self, limit: int = 10, min_importance: float = 0.0,
                      tags: List[str] = None, days_back: Optional[int] = None,
                      persona: Optional[str] = None) -> List[Dict]:
        """Recall episodic memories with filtering
        
        Args:
            limit: Maximum number of memories to return
            min_importance: Minimum importance score
            tags: Filter by tags (OR logic)
            days_back: Only return memories from last N days
            persona: Filter by persona name (prevents cross-contamination)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT id, timestamp, content, context, importance_score, 
                   emotional_valence, emotional_arousal, tags, relationship_context
            FROM episodic_memories
            WHERE importance_score >= ?
        """
        params = [min_importance]
        
        # Filter by persona to prevent cross-contamination
        if persona:
            query += " AND relationship_context LIKE ?"
            params.append(f"%persona:{persona}%")
        
        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            query += " AND timestamp >= ?"
            params.append(cutoff_date.isoformat())
        
        if tags:
            # Simple tag matching (can be enhanced)
            tag_conditions = " OR ".join(["tags LIKE ?" for _ in tags])
            query += f" AND ({tag_conditions})"
            params.extend([f"%{tag}%" for tag in tags])
        
        query += " ORDER BY importance_score DESC, timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        memories = []
        for row in rows:
            memories.append({
                'id': row[0],
                'timestamp': row[1],
                'content': row[2],
                'context': row[3],
                'importance_score': row[4],
                'emotional_valence': row[5],
                'emotional_arousal': row[6],
                'tags': json.loads(row[7]) if row[7] else [],
                'relationship_context': row[8]
            })
        
        conn.close()
        return memories
    
    def recall_semantic(self, key: Optional[str] = None, 
                       category: Optional[str] = None) -> Dict:
        """Recall semantic memories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if key:
            cursor.execute("""
                SELECT key, value, confidence, last_accessed, access_count
                FROM semantic_memories
                WHERE key = ?
            """, (key,))
            row = cursor.fetchone()
            if row:
                # Update access time
                cursor.execute("""
                    UPDATE semantic_memories 
                    SET last_accessed = CURRENT_TIMESTAMP,
                        access_count = access_count + 1
                    WHERE key = ?
                """, (key,))
                conn.commit()
                
                return {
                    'key': row[0],
                    'value': row[1],
                    'confidence': row[2],
                    'last_accessed': row[3],
                    'access_count': row[4]
                }
        else:
            cursor.execute("""
                SELECT key, value, confidence FROM semantic_memories
                ORDER BY access_count DESC, last_accessed DESC
            """)
            rows = cursor.fetchall()
            return {row[0]: {'value': row[1], 'confidence': row[2]} for row in rows}
        
        conn.close()
        return {}
    
    def get_relationship_summary(self) -> Dict:
        """Get a summary of the relationship"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count total interactions
        cursor.execute("SELECT COUNT(*) FROM episodic_memories")
        total_interactions = cursor.fetchone()[0]
        
        # Get milestones
        cursor.execute("""
            SELECT milestone_type, description, timestamp, significance
            FROM relationship_milestones
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        milestones = cursor.fetchall()
        
        # Get emotional patterns
        cursor.execute("""
            SELECT emotion_type, AVG(intensity) as avg_intensity, COUNT(*) as count
            FROM emotional_memories
            GROUP BY emotion_type
            ORDER BY count DESC
        """)
        emotional_patterns = cursor.fetchall()
        
        # Get preferences count
        cursor.execute("SELECT COUNT(*) FROM user_preferences")
        preferences_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_interactions': total_interactions,
            'milestones': [{
                'type': m[0],
                'description': m[1],
                'timestamp': m[2],
                'significance': m[3]
            } for m in milestones],
            'emotional_patterns': [{
                'emotion': e[0],
                'avg_intensity': e[1],
                'frequency': e[2]
            } for e in emotional_patterns],
            'preferences_learned': preferences_count
        }
    
    def consolidate_memories(self, days_threshold: int = 30):
        """
        Consolidate old memories into semantic knowledge
        This simulates how human memory works - converting episodic to semantic
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        # Find unconsolidated memories older than threshold
        cursor.execute("""
            SELECT id, content, context, importance_score
            FROM episodic_memories
            WHERE consolidated = 0 AND timestamp < ?
            ORDER BY importance_score DESC
        """, (cutoff_date.isoformat(),))
        
        memories_to_consolidate = cursor.fetchall()
        
        for memory_id, content, context, importance in memories_to_consolidate:
            # Extract key facts and store as semantic memories
            # This is a simplified version - could use NLP for better extraction
            if importance > 0.7:  # High importance memories
                # Create semantic memory from important episodic memory
                semantic_key = f"important_event_{memory_id}"
                self.remember_semantic(semantic_key, content, confidence=importance, 
                                      source_memory_id=memory_id)
            
            # Mark as consolidated
            cursor.execute("""
                UPDATE episodic_memories SET consolidated = 1 WHERE id = ?
            """, (memory_id,))
        
        conn.commit()
        conn.close()
    
    def find_related_memories(self, memory_id: int, limit: int = 5, persona: Optional[str] = None) -> List[Dict]:
        """Find memories related to a given memory
        
        Args:
            memory_id: ID of the memory to find related memories for
            limit: Maximum number of related memories to return
            persona: Filter by persona name (prevents cross-contamination)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get the target memory (including persona context)
        cursor.execute("SELECT tags, content, relationship_context FROM episodic_memories WHERE id = ?", (memory_id,))
        target = cursor.fetchall()
        if not target:
            return []
        
        target_tags = json.loads(target[0][0]) if target[0][0] else []
        target_content = target[0][1]
        target_persona = target[0][2]  # Extract persona from relationship_context
        
        # Extract persona from relationship_context if not provided
        if not persona and target_persona:
            # relationship_context format: "conversation|persona:Alex Mercer"
            if "persona:" in target_persona:
                persona = target_persona.split("persona:")[-1].split("|")[0].strip()
        
        # Build query with persona filtering
        persona_filter = ""
        params = []
        if persona:
            persona_filter = " AND relationship_context LIKE ?"
            params.append(f"%persona:{persona}%")
        
        # Find memories with similar tags or content
        if target_tags:
            tag_conditions = " OR ".join(["tags LIKE ?" for _ in target_tags])
            cursor.execute(f"""
                SELECT id, content, importance_score
                FROM episodic_memories
                WHERE id != ? AND ({tag_conditions}){persona_filter}
                ORDER BY importance_score DESC
                LIMIT ?
            """, [memory_id] + [f"%{tag}%" for tag in target_tags] + params + [limit])
        else:
            # Fallback to content similarity (simple keyword matching)
            keywords = set(target_content.lower().split()[:5])  # First 5 words
            keyword_conditions = " OR ".join(["content LIKE ?" for _ in keywords])
            cursor.execute(f"""
                SELECT id, content, importance_score
                FROM episodic_memories
                WHERE id != ? AND ({keyword_conditions}){persona_filter}
                ORDER BY importance_score DESC
                LIMIT ?
            """, [memory_id] + [f"%{kw}%" for kw in keywords] + params + [limit])
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'content': row[1],
            'importance_score': row[2]
        } for row in rows]
    
    def remember_media(self, memory_id: int, media_type: str, file_path: str,
                      description: str = "", transcription: str = "",
                      metadata: Dict = None) -> int:
        """
        Store a media file (image, audio, video) associated with a memory
        
        Args:
            memory_id: ID of the associated episodic memory
            media_type: 'image', 'audio', or 'video'
            file_path: Path to the media file
            description: Text description of the media
            transcription: For audio/video, transcribed text
            metadata: Additional metadata (dimensions, duration, etc.)
        
        Returns:
            Media memory ID
        """
        import shutil
        from pathlib import Path
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)
        file_size = os.path.getsize(file_path)
        
        # Get MIME type
        mime_type = self._get_mime_type(file_path)
        
        # Copy file to media directory
        file_ext = Path(file_path).suffix
        safe_filename = f"{memory_id}_{file_hash[:8]}{file_ext}"
        
        if media_type == "image":
            dest_dir = os.path.join(self.media_dir, "images")
        elif media_type == "audio":
            dest_dir = os.path.join(self.media_dir, "audio")
        else:
            dest_dir = os.path.join(self.media_dir, media_type)
            os.makedirs(dest_dir, exist_ok=True)
        
        dest_path = os.path.join(dest_dir, safe_filename)
        shutil.copy2(file_path, dest_path)
        
        # Generate thumbnail for images
        thumbnail_path = None
        if media_type == "image":
            thumbnail_path = self._generate_thumbnail(dest_path)
        
        metadata_str = json.dumps(metadata) if metadata else None
        
        cursor.execute("""
            INSERT INTO media_memories 
            (memory_id, media_type, file_path, file_hash, file_size, mime_type,
             description, transcription, metadata, thumbnail_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (memory_id, media_type, dest_path, file_hash, file_size, mime_type,
              description, transcription, metadata_str, thumbnail_path))
        
        media_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return media_id
    
    def recall_media(self, memory_id: Optional[int] = None,
                    media_type: Optional[str] = None,
                    limit: int = 10) -> List[Dict]:
        """Recall media memories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT id, memory_id, media_type, file_path, file_hash, file_size,
                   mime_type, description, transcription, metadata, thumbnail_path, created_at
            FROM media_memories
            WHERE 1=1
        """
        params = []
        
        if memory_id:
            query += " AND memory_id = ?"
            params.append(memory_id)
        
        if media_type:
            query += " AND media_type = ?"
            params.append(media_type)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'memory_id': row[1],
            'media_type': row[2],
            'file_path': row[3],
            'file_hash': row[4],
            'file_size': row[5],
            'mime_type': row[6],
            'description': row[7],
            'transcription': row[8],
            'metadata': json.loads(row[9]) if row[9] else {},
            'thumbnail_path': row[10],
            'created_at': row[11]
        } for row in rows]
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type of file"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"
    
    def _generate_thumbnail(self, image_path: str, size: Tuple[int, int] = (200, 200)) -> Optional[str]:
        """Generate thumbnail for image"""
        try:
            from PIL import Image
            
            img = Image.open(image_path)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            thumbnail_dir = os.path.join(self.media_dir, "thumbnails")
            thumbnail_filename = f"thumb_{os.path.basename(image_path)}"
            thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)
            
            img.save(thumbnail_path, "JPEG", quality=85)
            return thumbnail_path
        except ImportError:
            # PIL not available, skip thumbnail
            return None
        except Exception:
            # Error generating thumbnail, skip
            return None
    
    def clear_all_memories(self, include_media: bool = True) -> Dict[str, int]:
        """
        Clear all memory data from the database
        
        Args:
            include_media: If True, also delete media files from disk
            
        Returns:
            Dictionary with counts of deleted items
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        counts = {}
        
        # Get counts before deletion
        cursor.execute("SELECT COUNT(*) FROM episodic_memories")
        counts['episodic'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM semantic_memories")
        counts['semantic'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM emotional_memories")
        counts['emotional'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM relationship_milestones")
        counts['milestones'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_preferences")
        counts['preferences'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversation_patterns")
        counts['patterns'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM memory_associations")
        counts['associations'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM media_memories")
        counts['media'] = cursor.fetchone()[0]
        
        # Delete in order (respecting foreign keys)
        cursor.execute("DELETE FROM memory_associations")
        cursor.execute("DELETE FROM media_memories")
        cursor.execute("DELETE FROM emotional_memories")
        cursor.execute("DELETE FROM semantic_memories")
        cursor.execute("DELETE FROM conversation_patterns")
        cursor.execute("DELETE FROM relationship_milestones")
        cursor.execute("DELETE FROM user_preferences")
        cursor.execute("DELETE FROM episodic_memories")
        
        conn.commit()
        conn.close()
        
        # Delete media files if requested
        if include_media:
            try:
                import shutil
                if os.path.exists(self.media_dir):
                    shutil.rmtree(self.media_dir)
                    os.makedirs(self.media_dir, exist_ok=True)
                    os.makedirs(os.path.join(self.media_dir, "images"), exist_ok=True)
                    os.makedirs(os.path.join(self.media_dir, "audio"), exist_ok=True)
                    os.makedirs(os.path.join(self.media_dir, "thumbnails"), exist_ok=True)
            except Exception as e:
                print(f"Warning: Could not delete media files: {e}")
        
        return counts
    
    def clear_old_memories(self, days_old: int = 90, min_importance: float = 0.3) -> Dict[str, int]:
        """
        Clear old, low-importance memories
        
        Args:
            days_old: Delete memories older than this many days
            min_importance: Only delete memories with importance below this threshold
            
        Returns:
            Dictionary with counts of deleted items
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Find old, low-importance memories
        cursor.execute("""
            SELECT id FROM episodic_memories
            WHERE timestamp < ? AND importance_score < ?
        """, (cutoff_date.isoformat(), min_importance))
        
        memory_ids = [row[0] for row in cursor.fetchall()]
        
        if not memory_ids:
            return {'episodic': 0, 'semantic': 0, 'emotional': 0, 'media': 0}
        
        counts = {'episodic': len(memory_ids)}
        
        # Delete related data
        placeholders = ','.join(['?'] * len(memory_ids))
        
        cursor.execute(f"DELETE FROM memory_associations WHERE memory_id_1 IN ({placeholders}) OR memory_id_2 IN ({placeholders})", memory_ids + memory_ids)
        counts['associations'] = cursor.rowcount
        
        cursor.execute(f"DELETE FROM media_memories WHERE memory_id IN ({placeholders})", memory_ids)
        counts['media'] = cursor.rowcount
        
        cursor.execute(f"DELETE FROM emotional_memories WHERE memory_id IN ({placeholders})", memory_ids)
        counts['emotional'] = cursor.rowcount
        
        cursor.execute(f"DELETE FROM semantic_memories WHERE source_memory_id IN ({placeholders})", memory_ids)
        counts['semantic'] = cursor.rowcount
        
        # Delete the episodic memories
        cursor.execute(f"DELETE FROM episodic_memories WHERE id IN ({placeholders})", memory_ids)
        
        conn.commit()
        conn.close()
        
        return counts
