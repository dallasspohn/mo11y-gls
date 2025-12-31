# Mo11y Architecture - Technical Overview

## System Overview

Mo11y is built as a **lifelong companion AI** using a sophisticated architecture that enables:
- Long-term memory persistence
- Personality evolution
- Relationship building
- Proactive engagement

## Core Components

### 1. Enhanced Memory System (`enhanced_memory.py`)

A multi-layered memory system inspired by human memory:

#### Memory Types

**Episodic Memory**
- Stores specific events and conversations
- Includes: content, context, timestamp, importance score
- Tracks emotional valence and arousal
- Tagged for retrieval

**Semantic Memory**
- Stores facts and knowledge about the user
- Key-value pairs with confidence scores
- Linked to source episodic memories
- Tracks access frequency

**Emotional Memory**
- Records emotional states and patterns
- Tracks emotion type, intensity, triggers
- Linked to episodic memories
- Used for sentiment analysis

**Relationship Memory**
- Milestones and significant moments
- Tracks relationship dynamics
- Significance scoring
- Timeline of relationship growth

#### Database Schema

```sql
-- Episodic memories
episodic_memories (id, timestamp, content, context, importance_score, 
                   emotional_valence, emotional_arousal, tags, 
                   relationship_context, consolidated)

-- Semantic memories  
semantic_memories (id, key, value, confidence, source_memory_id, 
                   last_accessed, access_count, created_at)

-- Emotional memories
emotional_memories (id, timestamp, emotion_type, intensity, 
                    context, trigger, memory_id)

-- Relationship milestones
relationship_milestones (id, milestone_type, description, 
                        timestamp, significance, associated_memories)

-- User preferences
user_preferences (category, preference_key, preference_value, 
                  confidence, last_updated)
```

### 2. Companion Personality Engine (`companion_engine.py`)

Manages Mo11y's evolving personality:

#### Personality Traits
- **warmth**: How warm and caring Mo11y is
- **playfulness**: Level of humor and fun
- **empathy**: Understanding and emotional intelligence
- **directness**: How straightforward responses are
- **humor**: Use of humor in responses
- **proactivity**: How often Mo11y initiates
- **supportiveness**: Level of encouragement
- **curiosity**: Interest in learning about you

#### Evolution Mechanism
- Traits adjust based on interaction context
- Positive feedback increases warmth/supportiveness
- Negative feedback increases empathy
- Communication style preferences are learned
- Relationship dynamics tracked separately

### 3. LangGraph Agent (`mo11y_agent.py`)

Stateful agent workflow using LangGraph:

#### Workflow Nodes

1. **analyze_input**: Extracts sentiment, topics, context
2. **retrieve_memories**: Finds relevant episodic/semantic memories
3. **get_personality_context**: Loads current personality state
4. **generate_response**: Creates response with full context
5. **store_memory**: Saves interaction as episodic memory
6. **adapt_personality**: Updates traits based on interaction
7. **check_proactivity**: Decides if proactive engagement needed

#### State Flow

```
User Input → Analyze → Retrieve Memories → Get Personality 
→ Generate Response → Store Memory → Adapt Personality 
→ Check Proactivity → Response
```

#### Fallback Mode
If LangGraph unavailable, runs nodes sequentially (same functionality).

### 4. Relationship Timeline (`relationship_timeline.py`)

Visualization tools for relationship insights:

- **Interaction Timeline**: Daily interaction counts over time
- **Sentiment Heatmap**: Emotional patterns by day/week
- **Milestone Timeline**: Significant relationship moments
- **Personality Radar**: Current trait visualization
- **Memory Distribution**: Importance score analysis

### 5. Enhanced UI (`app_enhanced.py`)

Streamlit-based interface with:

#### Pages
- **Chat**: Main conversation interface
- **Relationship**: Stats, milestones, visualizations
- **Memories**: Searchable memory vault
- **Settings**: Personality and data management

#### Features
- Beautiful gradient design
- Real-time conversation display
- Proactive suggestions
- Interactive visualizations
- Memory search and filtering

## Data Flow

### Conversation Flow

```
1. User sends message
2. Agent analyzes input (sentiment, topics)
3. Retrieves relevant memories
4. Loads personality context
5. Generates response with LLM
6. Stores interaction as memory
7. Adapts personality traits
8. Checks for proactive engagement
9. Returns response + suggestions
```

### Memory Consolidation

```
Episodic Memory (30+ days old)
    ↓
High Importance (>0.7)
    ↓
Extract Key Facts
    ↓
Store as Semantic Memory
    ↓
Mark as Consolidated
```

### Personality Adaptation

```
Interaction Context
    ↓
User Sentiment Analysis
    ↓
Response Type Detection
    ↓
Adjust Trait Values
    ↓
Update Relationship Dynamics
```

## Key Design Decisions

### 1. Multi-Layered Memory
- Separates episodic (events) from semantic (facts)
- Enables better retrieval and consolidation
- Mimics human memory structure

### 2. Personality Evolution
- Traits evolve based on interactions
- Not static - adapts to user preferences
- Creates unique relationship over time

### 3. LangGraph Architecture
- Stateful workflow enables complex reasoning
- Checkpointing allows state persistence
- Extensible node system

### 4. Importance Scoring
- Memories scored for relevance
- High-importance memories prioritized
- Enables memory consolidation

### 5. Proactive Engagement
- Suggests topics based on history
- Recalls important memories
- Celebrates milestones

## Extensibility

### Adding New Memory Types
1. Add table to `enhanced_memory.py`
2. Add methods for storage/retrieval
3. Integrate into agent workflow

### Adding Personality Traits
1. Add to `personality_traits` table
2. Update adaptation logic in `companion_engine.py`
3. Add visualization in `relationship_timeline.py`

### Adding Workflow Nodes
1. Create node function in `mo11y_agent.py`
2. Add to graph in `_build_graph()`
3. Connect edges appropriately

## Performance Considerations

### Memory Management
- Consolidation runs periodically (30+ day threshold)
- Importance scoring filters low-value memories
- Semantic memory limits redundant storage

### Database Optimization
- Indexed on timestamp, importance_score
- Access tracking for semantic memories
- Efficient queries with limits

### LLM Usage
- Context window management
- Memory retrieval limits (top N)
- Streaming responses

## Future Enhancements

### Planned Features
- [ ] Vector embeddings for semantic search
- [ ] Multi-modal memory (images, audio)
- [ ] Advanced sentiment analysis (transformers)
- [ ] Memory export/import
- [ ] Custom personality training
- [ ] External API integrations
- [ ] Mobile app
- [ ] Voice interaction

### Research Areas
- Better memory consolidation algorithms
- Personality trait interaction modeling
- Proactive engagement optimization
- Long-term relationship dynamics

## Conclusion

Mo11y's architecture is designed for **lifelong companionship**:
- Persistent memory that grows over time
- Evolving personality that adapts
- Relationship tracking and milestones
- Beautiful, intimate interface

The system is modular, extensible, and designed to create a genuine relationship that deepens over time.

---

**Built with 💝 for lifelong companionship**
