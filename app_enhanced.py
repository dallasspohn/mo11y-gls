"""
Mo11y Enhanced - A Lifelong Companion
Streamlit interface with LangGraph agent integration
"""

# Suppress ScriptRunContext warning when running in bare mode
import warnings
warnings.filterwarnings("ignore", message=".*missing ScriptRunContext.*")

import streamlit as st
import json
import sqlite3
import datetime
import os
import tempfile
import random
import re
from typing import Optional
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from mo11y_agent import create_mo11y_agent
from enhanced_memory import EnhancedMemory
from companion_engine import CompanionPersonality
from relationship_timeline import RelationshipTimeline

# Page config
st.set_page_config(
    page_title="Mo11y - Your Lifelong Companion",
    page_icon="💝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a more intimate, companion-like feel
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Color+Emoji&display=swap');
    
    * {
        font-family: 'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', 'EmojiOne Color', 'Twemoji Mozilla', 'Segoe UI Symbol', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .companion-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        word-wrap: break-word;
    }
    .companion-message ul,
    .companion-message ol {
        margin: 0.75rem 0;
        padding-left: 2rem;
        list-style-position: outside;
        display: block;
    }
    .companion-message ul {
        list-style-type: disc;
    }
    .companion-message ol {
        list-style-type: decimal;
    }
    .companion-message li {
        margin: 0.5rem 0;
        display: list-item;
        line-height: 1.5;
    }
    .companion-message p {
        margin: 0.75rem 0;
        line-height: 1.6;
    }
    .companion-message p:first-child {
        margin-top: 0;
    }
    .companion-message p:last-child {
        margin-bottom: 0;
    }
    .companion-message br {
        display: block;
        content: "";
        margin: 0.5rem 0;
    }
    .user-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .milestone-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .memory-card {
        background: #f8f9fa;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #667eea;
    }
    h1 {
        color: #667eea;
        text-align: center;
    }
    .relationship-stats {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
@st.cache_resource
def load_config():
    config_path = "config.json"
    
    # Get base directory (where script is running)
    base_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
    
    # Default config with relative paths (can be overridden by env vars or config.json)
    default_config = {
        "sonas_dir": os.getenv("MO11Y_SONAS_DIR", os.path.join(base_dir, "sonas")),
        "rags_dir": os.getenv("MO11Y_RAGS_DIR", os.path.join(base_dir, "RAGs")),
        "texts_dir": os.getenv("MO11Y_TEXTS_DIR", os.path.join(base_dir, "text")),
        "db_path": os.getenv("MO11Y_DB_PATH", os.path.join(base_dir, "mo11y_companion.db")),
        "model_name": os.getenv("MO11Y_MODEL_NAME", "deepseek-r1:latest"),
    }
    
    # Normalize paths (expand relative paths, ensure trailing slashes for dirs)
    for key in ["sonas_dir", "rags_dir", "texts_dir"]:
        if default_config[key] and not os.path.isabs(default_config[key]):
            default_config[key] = os.path.abspath(default_config[key])
        if not default_config[key].endswith(os.sep):
            default_config[key] += os.sep
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                user_config = json.load(f)
                # Merge user config, but normalize paths
                merged_config = {**default_config, **user_config}
                
                # Normalize paths from user config
                for key in ["sonas_dir", "rags_dir", "texts_dir"]:
                    if key in merged_config and merged_config[key]:
                        if not os.path.isabs(merged_config[key]):
                            merged_config[key] = os.path.abspath(merged_config[key])
                        if not merged_config[key].endswith(os.sep):
                            merged_config[key] += os.sep
                
                return merged_config
        except:
            return default_config
    return default_config

CONFIG = load_config()

# Helper function to get all available sona files
def get_available_sonas():
    """Get list of all available sona files"""
    # Get base directory for fallback
    base_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
    sonas_dir = CONFIG.get("sonas_dir", os.path.join(base_dir, "sonas"))
    sonas = {}
    
    if os.path.exists(sonas_dir):
        for filename in os.listdir(sonas_dir):
            if filename.endswith(".json") and not filename.startswith("."):
                sona_path = os.path.join(sonas_dir, filename)
                try:
                    with open(sona_path, "r") as f:
                        sona_data = json.load(f)
                    # Get display name from sona file
                    display_name = sona_data.get("name", filename.replace(".json", "").replace("-", " ").title())
                    
                    # Check for persona image
                    image_path = None
                    # Get base directory for path resolution
                    try:
                        base_dir = os.path.dirname(os.path.abspath(__file__))
                    except NameError:
                        base_dir = os.getcwd()
                    
                    # Check if image_path is specified in sona file
                    if "image_path" in sona_data:
                        image_path = sona_data["image_path"]
                        # If relative path, make it relative to project root
                        if not os.path.isabs(image_path):
                            image_path = os.path.join(base_dir, image_path)
                    else:
                        # Try default location: media/images/{persona_name}.{jpg|png|webp}
                        images_dir = os.path.join(base_dir, "media", "images")
                        persona_name_lower = display_name.lower().replace(" ", "_").replace("-", "_")
                        for ext in ["jpg", "jpeg", "png", "webp"]:
                            default_image = os.path.join(images_dir, f"{persona_name_lower}.{ext}")
                            if os.path.exists(default_image):
                                image_path = default_image
                                break
                    
                    sonas[display_name] = {
                        "path": sona_path,
                        "filename": filename,
                        "description": sona_data.get("description", ""),
                        "image_path": image_path if image_path and os.path.exists(image_path) else None
                    }
                except Exception as e:
                    # Skip invalid JSON files
                    continue
    
    # Sort by name
    return dict(sorted(sonas.items()))

# Initialize agent (cached with persona key)
# Helper function to get spinner message based on persona/model
def get_spinner_message(persona_name: str, model_name: str = None) -> str:
    """Get contextual spinner message, especially for isekai personas"""
    # Check if using jim-spohn model
    if model_name and "jim-spohn" in model_name.lower():
        isekai_messages = [
            f"{persona_name} is using the World-Bridge Crystal...",
            f"{persona_name} is channeling magic...",
            f"{persona_name} is currently being chased by an ice dragon...",
            f"{persona_name} is consulting the Adventurer's Guild...",
            f"{persona_name} is checking quest logs...",
            f"{persona_name} is casting a communication spell...",
            f"{persona_name} is dodging goblins...",
            f"{persona_name} is enchanting a message...",
            f"{persona_name} is traversing dimensions...",
            f"{persona_name} is consulting ancient runes...",
            f"{persona_name} is setting up traps...",
            f"{persona_name} is tracking monsters...",
            f"{persona_name} is polishing the World-Bridge Crystal...",
            f"{persona_name} is reading scrolls...",
            f"{persona_name} is preparing for a quest...",
            f"{persona_name} is wondering about other reincarnated heroes...",
            f"{persona_name} is pondering other worlds...",
        ]
        return random.choice(isekai_messages)
    
    # Default message for other personas
    return f"{persona_name} is thinking..."

# Note: Cache is cleared when persona changes, but preferences update requires page refresh
# Cache key includes a version to force refresh when code changes
@st.cache_resource
def get_agent(sona_path_key: str = None, _cache_version: str = "v2.0"):
    """Get agent instance, cached by persona path"""
    sona_path = None
    persona_name = "Default"
    
    if sona_path_key and sona_path_key != "None":
        sona_path = sona_path_key
        # Extract persona name from path
        filename = os.path.basename(sona_path).replace(".json", "")
        persona_name = filename.replace("-", " ").title()
        # Try to get actual name from sona file
        try:
            with open(sona_path, "r") as f:
                sona_data = json.load(f)
                persona_name = sona_data.get("name", persona_name)
        except:
            pass
    
    # Check for per-persona model configuration
    model_name = CONFIG["model_name"]
    if sona_path:
        try:
            with open(sona_path, "r") as f:
                sona_data = json.load(f)
                # Check if persona has a specific model configured
                if "model_name" in sona_data:
                    model_name = sona_data["model_name"]
                    print(f"Using per-sona model: {model_name} for {persona_name}")
        except:
            pass
    
    # Ensure database path is absolute and consistent
    base_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
    db_path = CONFIG.get("db_path", os.path.join(base_dir, "SPOHNZ.db"))
    if not os.path.isabs(db_path):
        # Convert relative path to absolute
        db_path = os.path.abspath(db_path)
    
    # Get rags_dir with fallback
    rags_dir = CONFIG.get("rags_dir")
    if not rags_dir:
        rags_dir = os.path.join(base_dir, "RAGs")
    if not os.path.isabs(rags_dir):
        rags_dir = os.path.abspath(rags_dir)
    
    # Debug: Print database path being used
    print(f"Using database: {db_path}")
    print(f"Using RAGs directory: {rags_dir}")
    
    return create_mo11y_agent(
        model_name=model_name,
        db_path=db_path,
        sona_path=sona_path,
        suppress_thinking=CONFIG.get("suppress_thinking", True),  # Default to True
        rags_dir=rags_dir
    ), persona_name

# Initialize session state for persona selection
if "selected_persona" not in st.session_state:
    # Default to Mo11y if available, otherwise first available sona
    available_sonas = get_available_sonas()
    if "Mo11y" in available_sonas:
        st.session_state.selected_persona = "Mo11y"
    elif available_sonas:
        st.session_state.selected_persona = list(available_sonas.keys())[0]
    else:
        st.session_state.selected_persona = "None (Default)"

# Get available sonas for sidebar (will be used in sidebar)
available_sonas_for_sidebar = get_available_sonas()

# Get selected persona path (before sidebar, so we can initialize agent)
selected_persona_name = st.session_state.get("selected_persona", "Mo11y")
if selected_persona_name == "None (Default)":
    selected_sona_path = None
else:
    selected_sona_path = available_sonas_for_sidebar.get(selected_persona_name, {}).get("path") if selected_persona_name in available_sonas_for_sidebar else None

# Get agent with selected persona (cache key includes persona path)
# Clear cache if needed (uncomment to force refresh)
# get_agent.clear()
agent, current_persona_name = get_agent(selected_sona_path)

# Track persona changes (but don't clear conversation history - each persona has its own)
if "previous_persona" not in st.session_state:
    st.session_state.previous_persona = current_persona_name
elif st.session_state.previous_persona != current_persona_name:
    # Persona changed - switch to that persona's conversation history
    st.session_state.previous_persona = current_persona_name

st.session_state.current_persona = current_persona_name

memory = agent.memory
personality = agent.personality
timeline = RelationshipTimeline(memory)

# Initialize per-persona conversation histories (dict keyed by persona name)
if "conversation_histories" not in st.session_state:
    st.session_state.conversation_histories = {}
if "agent_states" not in st.session_state:
    st.session_state.agent_states = {}
if "thread_ids" not in st.session_state:
    st.session_state.thread_ids = {}

# Initialize conversation history for current persona if it doesn't exist
if current_persona_name not in st.session_state.conversation_histories:
    st.session_state.conversation_histories[current_persona_name] = []
if current_persona_name not in st.session_state.agent_states:
    st.session_state.agent_states[current_persona_name] = {}
if current_persona_name not in st.session_state.thread_ids:
    st.session_state.thread_ids[current_persona_name] = f"thread_{current_persona_name.lower().replace(' ', '_')}"

# Get current persona's conversation history and thread_id
conversation_history = st.session_state.conversation_histories[current_persona_name]
thread_id = st.session_state.thread_ids[current_persona_name]

# Sidebar
with st.sidebar:
    # Persona Selector
    st.subheader("🎭 Select Persona")
    
    if available_sonas_for_sidebar:
        # Create list of persona names for selector (Mo11y first, then others)
        other_personas = [p for p in available_sonas_for_sidebar.keys() if p != "Mo11y"]
        persona_options = ["Mo11y"] + other_personas if "Mo11y" in available_sonas_for_sidebar else list(available_sonas_for_sidebar.keys())
        
        # Get current selection index
        current_index = 0
        current_selection = st.session_state.get("selected_persona", "Mo11y")
        if current_selection in persona_options:
            current_index = persona_options.index(current_selection)
        elif "Mo11y" in persona_options:
            current_index = persona_options.index("Mo11y")
        
        # Persona selector dropdown
        selected_persona = st.selectbox(
            "Choose a persona:",
            options=persona_options,
            index=current_index,
            label_visibility="collapsed",
            key="persona_selector"
        )
        
        # Update session state if selection changed
        if selected_persona != st.session_state.selected_persona:
            st.session_state.selected_persona = selected_persona
            # Don't clear conversation history - each persona maintains its own
            # Just clear agent cache to reload with new persona
            get_agent.clear()
            st.rerun()
        
        # Show selected persona info
        if selected_persona and selected_persona != "None (Default)":
            persona_info = available_sonas_for_sidebar.get(selected_persona, {})
            persona_name = selected_persona
            
            # Display persona image if available (instead of or alongside description)
            image_path = persona_info.get("image_path")
            if image_path and os.path.exists(image_path):
                try:
                    st.image(image_path, use_container_width=True, caption=persona_name)
                except Exception as e:
                    # If image fails to load, fall back to text
                    st.error(f"Could not load image: {str(e)}")
                    if persona_name == "Alex Mercer":
                        st.title("👩 Alex Mercer")
                        st.caption("Personal Assistant")
                    elif persona_name == "Izzy-Chan":
                        st.title("💋 Izzy-Chan")
                        st.caption("Sassy & Flirtatious")
                    elif persona_name == "Mo11y":
                        st.title("💝 Mo11y")
                        st.caption("Your Lifelong Companion")
                    else:
                        st.title(f"🎭 {persona_name}")
            else:
                # Display persona name and description (no image available)
                if persona_name == "Alex Mercer":
                    st.title("👩 Alex Mercer")
                    st.caption("Personal Assistant")
                elif persona_name == "Izzy-Chan":
                    st.title("💋 Izzy-Chan")
                    st.caption("Sassy & Flirtatious")
                elif persona_name == "Mo11y":
                    st.title("💝 Mo11y")
                    st.caption("Your Lifelong Companion")
                else:
                    st.title(f"🎭 {persona_name}")
            
            # Show description in expander if image is shown, or normally if no image
            if persona_info.get("description"):
                if image_path and os.path.exists(image_path):
                    # If image is shown, put description in expander
                    with st.expander("📝 Persona Description"):
                        st.caption(persona_info["description"][:200] + "..." if len(persona_info["description"]) > 200 else persona_info["description"])
                else:
                    # If no image, show description normally
                    with st.expander("📝 Persona Description"):
                        st.caption(persona_info["description"][:200] + "..." if len(persona_info["description"]) > 200 else persona_info["description"])
        else:
            st.title("🤖 Default")
            st.caption("No persona selected")
    else:
        st.warning("No persona files found in sonas directory")
        st.title("🤖 Default")
    
    st.markdown("---")
    
    # Relationship stats
    relationship_summary = memory.get_relationship_summary()
    st.metric("Total Interactions", relationship_summary["total_interactions"])
    st.metric("Preferences Learned", relationship_summary["preferences_learned"])
    
    # Media stats
    media_items = memory.recall_media(limit=100)
    if media_items:
        image_count = sum(1 for m in media_items if m['media_type'] == 'image')
        audio_count = sum(1 for m in media_items if m['media_type'] == 'audio')
        st.metric("Media Memories", f"{image_count} 📷 {audio_count} 🎵")
    
    st.markdown("---")
    
    # Display Preferences
    all_preferences = memory.get_all_preferences()
    if all_preferences:
        st.subheader("💭 Your Preferences")
        for category, prefs in all_preferences.items():
            with st.expander(f"{category.title()}", expanded=False):
                for key, pref_data in prefs.items():
                    st.write(f"**{key.replace('_', ' ').title()}**: {pref_data['value']}")
        st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigate",
        ["💬 Chat", "📊 Relationship", "🧠 Memories", "⚙️ Settings"],
        label_visibility="collapsed"
    )

# Main content based on page selection
if page == "💬 Chat":
    persona_name = st.session_state.get("current_persona", "Mo11y")
    selected_persona_name = st.session_state.get("selected_persona", "Mo11y") or "Mo11y"
    
    # Dynamic title based on selected persona
    if persona_name == "Alex Mercer" or selected_persona_name == "Alex Mercer":
        st.title("💬 Chat with Alex Mercer")
        st.markdown("*Your Personal Assistant*")
    elif persona_name == "Izzy-Chan" or selected_persona_name == "Izzy-Chan":
        st.title("💬 Chat with Izzy-Chan")
        st.markdown("*Sassy, confident, and flirtatious*")
    elif persona_name == "Mo11y" or selected_persona_name == "Mo11y":
        st.title("💬 Chat with Mo11y")
        st.markdown("*Your lifelong companion who grows with you*")
    else:
        st.title(f"💬 Chat with {persona_name}")
        # Get description from available sonas
        available_sonas = get_available_sonas()
        persona_info = available_sonas.get(selected_persona_name, {})
        description = persona_info.get("description", "")
        if description:
            st.markdown(f"*{description[:100]}...*" if len(description) > 100 else f"*{description}*")
    
    # Display conversation history (for current persona)
    chat_container = st.container()
    with chat_container:
        for msg in conversation_history:
            if msg["role"] == "user":
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.markdown("**You:**")
                with col2:
                    # Add timestamp if available
                    timestamp_str = ""
                    if "timestamp" in msg:
                        timestamp_str = f'<small style="opacity: 0.7;">{msg["timestamp"]}</small><br>'
                    st.markdown(f'<div class="user-message">{timestamp_str}{msg["content"]}</div>', 
                              unsafe_allow_html=True)
                    
                    # Display media if present
                    if "media" in msg:
                        for media_item in msg["media"]:
                            file_path = media_item.get("path")
                            if not file_path:
                                continue
                                
                            # Check if file exists, if not try to find in memory
                            if not os.path.exists(file_path):
                                # Try to find in recent media memories
                                # Get recent episodic memories first to narrow down the search
                                recent_memories = memory.recall_episodic(limit=5)
                                found_media = None
                                
                                # Try to find media associated with recent memories
                                for mem in recent_memories:
                                    mem_media = memory.recall_media(
                                        memory_id=mem['id'],
                                        media_type=media_item["type"],
                                        limit=1
                                    )
                                    if mem_media and os.path.exists(mem_media[0]['file_path']):
                                        found_media = mem_media[0]
                                        break
                                
                                # If not found in recent memories, try general search
                                if not found_media:
                                    recent_media = memory.recall_media(
                                        media_type=media_item["type"],
                                        limit=5
                                    )
                                    for recent in recent_media:
                                        if os.path.exists(recent['file_path']):
                                            found_media = recent
                                            break
                                
                                if found_media:
                                    file_path = found_media['file_path']
                                    # Update description if available from memory
                                    if found_media.get('description'):
                                        media_item['description'] = found_media['description']
                                else:
                                    # File not found, skip displaying
                                    st.caption(f"⚠️ Media file not found: {media_item.get('description', 'uploaded file')}")
                                    continue
                            
                            # Display the media
                            if media_item["type"] == "image":
                                if os.path.exists(file_path):
                                    st.image(file_path, caption=media_item.get("description", ""), width=300)
                                else:
                                    st.caption(f"⚠️ Image not found: {media_item.get('description', 'uploaded image')}")
                            elif media_item["type"] == "audio":
                                if os.path.exists(file_path):
                                    st.audio(file_path)
                                    if media_item.get('description'):
                                        st.caption(media_item['description'])
                                else:
                                    st.caption(f"⚠️ Audio file not found: {media_item.get('description', 'uploaded audio')}")
            else:
                col1, col2 = st.columns([1, 4])
                with col1:
                    companion_name = st.session_state.get("current_persona", "Mo11y")
                    # Use the actual persona name
                    display_name = companion_name
                    st.markdown(f"**{display_name}:**")
                with col2:
                    # Add timestamp if available
                    timestamp_str = ""
                    if "timestamp" in msg:
                        timestamp_str = f'<small style="opacity: 0.7;">{msg["timestamp"]}</small><br>'
                    
                    # Convert markdown to HTML for proper rendering
                    try:
                        import markdown
                        # Convert markdown to HTML with proper extensions
                        html_content = markdown.markdown(
                            msg["content"],
                            extensions=['nl2br', 'fenced_code']
                        )
                    except ImportError:
                        # Fallback: simple markdown conversion if library not available
                        import re
                        content = msg["content"]
                        # Convert **bold** to <strong>
                        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
                        # Convert *italic* to <em> (but not **bold**)
                        content = re.sub(r'(?<!\*)\*([^\*]+?)\*(?!\*)', r'<em>\1</em>', content)
                        # Convert line breaks
                        content = content.replace('\n', '<br>')
                        html_content = content
                    
                    st.markdown(
                        f'<div class="companion-message">{timestamp_str}{html_content}</div>', 
                        unsafe_allow_html=True
                    )
                    
                    # Display generated image if present
                    if "generated_image" in msg and os.path.exists(msg["generated_image"]):
                        st.image(msg["generated_image"], use_container_width=True, caption="Generated Image")
                        # Add download button
                        with open(msg["generated_image"], "rb") as img_file:
                            st.download_button(
                                label="📥 Download Image",
                                data=img_file.read(),
                                file_name=os.path.basename(msg["generated_image"]),
                                mime="image/png"
                            )
    
    # Chat input with file upload
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Your message:", height=100, placeholder="Ask me anything or request assistance...")
        
        # File uploader for images and audio
        col1, col2 = st.columns([3, 1])
        with col1:
            uploaded_files = st.file_uploader(
                "Attach image or audio (optional)",
                type=['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp3', 'wav', 'ogg', 'm4a'],
                accept_multiple_files=True,
                help="Upload images or audio files to include in your message"
            )
        with col2:
            st.write("")  # Spacing
        
        submitted = st.form_submit_button("Send 💝", use_container_width=True)
    
    if submitted and (user_input or uploaded_files):
        persona_name = st.session_state.get("current_persona", "Mo11y")
        
        # Handle commands (must be at start of message)
        user_message = user_input if user_input else "User shared media"
        command_handled = False
        
        # Check for commands
        if user_message.strip().startswith('/'):
            command_parts = user_message.strip().split(None, 1)
            command = command_parts[0].lower()  # Command is case-insensitive
            command_args = command_parts[1] if len(command_parts) > 1 else ""
            # Preserve original case of arguments (for filenames, etc.)
            original_args = command_parts[1] if len(command_parts) > 1 else ""
            
            # /journal command - save journal entry
            if command == '/journal':
                command_handled = True
                journal_text = command_args if command_args else user_message.replace('/journal', '').strip()
                
                if journal_text:
                    try:
                        # Save to journal (if available)
                        if hasattr(agent, 'journal') and agent.journal:
                            # Add as timeline entry (saves to journal.json only)
                            agent.journal.add_timeline_entry(
                                year=None,
                                content=journal_text,
                                context={"source": "command", "type": "journal_entry"}
                            )
                            
                            st.success("✅ Journal entry saved!")
                            # Show confirmation message
                            response = f"I've saved your journal entry: \"{journal_text[:100]}{'...' if len(journal_text) > 100 else ''}\"\n\nIt's been stored in journal.json for future reference."
                        else:
                            # Fallback if journal not available
                            st.warning("⚠️ Journal not available. Journal entry not saved.")
                            response = "I couldn't save your journal entry because the journal system is not available."
                        
                        # Add to conversation history
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        user_msg = {"role": "user", "content": user_message, "timestamp": timestamp}
                        conversation_history.append(user_msg)
                        conversation_history.append({"role": "assistant", "content": response, "timestamp": timestamp})
                        st.session_state.conversation_histories[current_persona_name] = conversation_history
                    except Exception as e:
                        st.error(f"❌ Error saving journal entry: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                else:
                    st.warning("⚠️ Please provide journal entry text after /journal")
            
            # Persona switching commands
            elif command == '/tool-builder' or command == '/toolbuilder':
                command_handled = True
                if "Tool Builder" in available_sonas_for_sidebar:
                    # Show available tools before switching
                    tools_list = ""
                    if agent.mcp_client:
                        try:
                            tools = agent.mcp_client.list_tools()
                            if tools:
                                tools_list = "\n\n**Available MCP Tools:**\n"
                                for i, tool in enumerate(tools, 1):
                                    tool_name = tool.get('name', 'Unknown')
                                    tool_desc = tool.get('description', 'No description')
                                    tools_list += f"{i}. **{tool_name}** - {tool_desc}\n"
                            else:
                                tools_list = "\n\n⚠️ No MCP tools available. Make sure the MCP server is running."
                        except Exception as e:
                            tools_list = f"\n\n⚠️ Could not retrieve tools: {str(e)}"
                    
                    # Add to conversation history
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    switch_message = f"Switching to Tool Builder persona.{tools_list}"
                    user_msg = {"role": "user", "content": user_message, "timestamp": timestamp}
                    conversation_history.append(user_msg)
                    conversation_history.append({"role": "assistant", "content": switch_message, "timestamp": timestamp})
                    st.session_state.conversation_histories[current_persona_name] = conversation_history
                    
                    # Display tools immediately
                    st.info("🛠️ Switching to Tool Builder persona...")
                    if tools_list:
                        st.markdown(tools_list)
                    
                    st.session_state.selected_persona = "Tool Builder"
                    get_agent.clear()
                    st.rerun()
                else:
                    st.error("Tool Builder persona not found")
            
            elif command == '/alex' or command == '/alex-mercer':
                command_handled = True
                if "Alex Mercer" in available_sonas_for_sidebar:
                    st.session_state.selected_persona = "Alex Mercer"
                    get_agent.clear()
                    st.rerun()
                else:
                    st.error("Alex Mercer persona not found")
            
            elif command == '/izzy' or command == '/izzy-chan':
                command_handled = True
                if "Izzy-Chan" in available_sonas_for_sidebar:
                    st.session_state.selected_persona = "Izzy-Chan"
                    get_agent.clear()
                    st.rerun()
                else:
                    st.error("Izzy-Chan persona not found")
            
            elif command == '/cjs' or command == '/jim':
                command_handled = True
                # Look for CJS persona by checking for "cjs" in filename or "Carroll" or "Jim" in name
                cjs_persona = None
                for persona_name, persona_info in available_sonas_for_sidebar.items():
                    filename_lower = persona_info.get("filename", "").lower()
                    name_lower = persona_name.lower()
                    if "cjs" in filename_lower or "carroll" in name_lower or ("jim" in name_lower and "carroll" in name_lower):
                        cjs_persona = persona_name
                        break
                
                if cjs_persona:
                    st.session_state.selected_persona = cjs_persona
                    get_agent.clear()
                    st.rerun()
                else:
                    st.error("CJS persona not found")
            
            elif command == '/mo11y':
                command_handled = True
                if "Mo11y" in available_sonas_for_sidebar:
                    st.session_state.selected_persona = "Mo11y"
                    get_agent.clear()
                    st.rerun()
                else:
                    st.error("Mo11y persona not found")
            
            elif command == '/quest' or command == '/adventure':
                command_handled = True
                # Quest system commands for CJS persona
                if current_persona_name.lower() in ["jimmy spohn", "cjs", "carroll james spohn"]:
                    try:
                        from sonas.jim_quest_system import JimQuestSystem
                        quest_system = JimQuestSystem(cjs_json_path=selected_sona_path)
                        
                        if not command_args or command_args.lower() in ["new", "generate"]:
                            # Generate new quest
                            quest = quest_system.generate_quest(rank="E")
                            quest_system.add_quest(quest)
                            
                            quest_info = f"""
**New Quest Generated!**

**Title:** {quest['title']}
**Type:** {quest['type'].replace('_', ' ').title()}
**Details:** {quest['details']}
**Location:** {quest['location']}
**Reward:** {quest['reward_gold']} gold pieces
**Additional Rewards:** {', '.join(quest['additional_rewards']) if quest['additional_rewards'] else 'None'}
**Difficulty:** {quest['difficulty']}
**Status:** {quest['status']}

Quest ID: {quest['quest_id']}
"""
                            response = quest_info
                            st.success("✅ New quest generated!")
                        elif command_args.lower() in ["list", "active", "current"]:
                            # List active quests
                            active_quests = quest_system.get_active_quests()
                            if active_quests:
                                quest_list = "**Active Quests:**\n\n"
                                for i, quest in enumerate(active_quests, 1):
                                    quest_list += f"{i}. **{quest['title']}**\n"
                                    quest_list += f"   Progress: {quest['progress']}% - {quest['progress_description']}\n"
                                    quest_list += f"   Reward: {quest['reward_gold']} gp\n"
                                    quest_list += f"   Status: {quest['status']}\n\n"
                                response = quest_list
                            else:
                                response = "No active quests. Use `/quest new` to generate one!"
                        elif command_args.lower().startswith("complete"):
                            # Complete a quest
                            parts = command_args.split()
                            if len(parts) > 1:
                                quest_id = parts[1]
                                completed = quest_system.complete_quest(quest_id, success=True)
                                if completed:
                                    response = f"✅ Quest completed! Earned {completed['reward_gold']} gold pieces.\n\n**Completed:** {completed['title']}"
                                    st.success("Quest completed!")
                                else:
                                    response = "❌ Quest not found or already completed."
                            else:
                                response = "Usage: `/quest complete <quest_id>`"
                        elif command_args.lower() == "summary" or command_args.lower() == "stats":
                            # Quest statistics
                            summary = quest_system.get_quest_summary()
                            stats = f"""
**Quest Statistics:**

- Active Quests: {summary['active_quests']}
- Total Completed: {summary['completed_quests']}
- Total Gold Earned: {summary['total_gold_earned']} gp

"""
                            if summary.get('recent_quests'):
                                stats += "**Recent Completed Quests:**\n"
                                for quest in summary['recent_quests'][-5:]:
                                    stats += f"- {quest['title']} ({quest.get('date_completed', 'Unknown')})\n"
                            response = stats
                        else:
                            response = "Quest commands:\n- `/quest new` - Generate new quest\n- `/quest list` - List active quests\n- `/quest complete <id>` - Complete a quest\n- `/quest stats` - View statistics"
                    except ImportError:
                        response = "Quest system not available. Make sure jim_quest_system.py exists."
                    except Exception as e:
                        response = f"Error with quest system: {str(e)}"
                        st.error(f"Quest system error: {str(e)}")
                else:
                    response = "Quest system is only available for Jimmy Spohn (CJS) persona."
                
                # Add to conversation history
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user_msg = {"role": "user", "content": user_message, "timestamp": timestamp}
                conversation_history.append(user_msg)
                conversation_history.append({"role": "assistant", "content": response, "timestamp": timestamp})
                st.session_state.conversation_histories[current_persona_name] = conversation_history
                st.markdown(response)
                st.rerun()
            
            elif command == '/help' or command == '/commands':
                command_handled = True
                # Try to read COMMANDS.md - use absolute path based on script location
                script_dir = os.path.dirname(os.path.abspath(__file__))
                commands_file = os.path.join(script_dir, "COMMANDS.md")
                help_text = ""
                
                if os.path.exists(commands_file):
                    try:
                        with open(commands_file, 'r', encoding='utf-8') as f:
                            help_text = f.read()
                    except Exception as e:
                        help_text = f"Error reading COMMANDS.md: {str(e)}\n\n## Available Commands\n\n**`/journal <text>`** - Save a journal entry\n**`/tool-builder`** - Switch to Tool Builder persona\n**`/alex`** - Switch to Alex Mercer persona\n**`/izzy`** - Switch to Izzy-Chan persona\n**`/cjs`** - Switch to CJS (Jim) persona\n**`/mo11y`** - Switch to Mo11y persona\n**`/help`** or **`/commands`** - Show this help message\n**`/docs`** - List available documentation files\n**`/read filename.md`** - Read any markdown file"
                else:
                    help_text = """
## Available Commands

**`/journal <text>`** - Save a journal entry  
**`/tool-builder`** - Switch to Tool Builder persona  
**`/alex`** - Switch to Alex Mercer persona  
**`/izzy`** - Switch to Izzy-Chan persona  
**`/cjs`** - Switch to CJS (Jim) persona  
**`/mo11y`** - Switch to Mo11y persona  
**`/quest`** - Quest system (Jim only): `/quest new`, `/quest list`, `/quest complete <id>`, `/quest stats`  
**`/help`** or **`/commands`** - Show this help message  
**`/docs`** - List available documentation files
**`/read filename.md`** or **`/show filename.md`** - Read any markdown file

For more details, see `COMMANDS.md` in the project root.
"""
                
                # Add to conversation history
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user_msg = {"role": "user", "content": user_message, "timestamp": timestamp}
                conversation_history.append(user_msg)
                conversation_history.append({"role": "assistant", "content": help_text, "timestamp": timestamp})
                st.session_state.conversation_histories[current_persona_name] = conversation_history
                # Display help immediately and rerun to show it
                st.markdown(help_text)
                st.rerun()
            
            elif command.startswith('/read') or command.startswith('/show'):
                command_handled = True
                # Extract filename from command: /read filename.md or /show filename.md
                # Use original_args to preserve case of filename
                # Get script directory - try multiple methods for Streamlit compatibility
                try:
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                except NameError:
                    # __file__ not available, use current working directory
                    script_dir = os.getcwd()
                
                # Extract filename from ORIGINAL user_message to preserve case (not lowercased command)
                original_parts = user_message.strip().split(None, 1)
                if len(original_parts) > 1:
                    md_filename = original_parts[1].strip()  # Preserve original case
                else:
                    md_filename = ""
                
                if md_filename:
                    if not md_filename.endswith('.md'):
                        md_filename += '.md'
                    
                    # Try multiple paths: script_dir, current dir, and just filename
                    possible_paths = [
                        os.path.join(script_dir, md_filename),
                        md_filename,
                        os.path.abspath(md_filename)
                    ]
                    
                    md_path = None
                    for path in possible_paths:
                        if os.path.exists(path) and os.path.isfile(path):
                            md_path = path
                            break
                    
                    # If exact match fails, try case-insensitive search
                    if not md_path:
                        search_dirs = [script_dir, os.getcwd()]
                        for search_dir in search_dirs:
                            if os.path.exists(search_dir):
                                try:
                                    for f in os.listdir(search_dir):
                                        if f.lower() == md_filename.lower() and f.endswith('.md'):
                                            md_path = os.path.join(search_dir, f)
                                            md_filename = f  # Use actual filename case
                                            break
                                    if md_path:
                                        break
                                except:
                                    pass
                    
                    if md_path:
                        try:
                            with open(md_path, 'r', encoding='utf-8') as f:
                                md_content = f.read()
                            help_text = f"Here's the {md_filename} file:\n\n{md_content}"
                        except Exception as e:
                            help_text = f"Error reading {md_filename}: {str(e)}\n\nTried path: {md_path}"
                    else:
                        # File not found - list available files
                        search_dirs = [script_dir, os.getcwd()]
                        md_files = []
                        for search_dir in search_dirs:
                            if os.path.exists(search_dir):
                                try:
                                    files = [f for f in os.listdir(search_dir) if f.endswith('.md') and os.path.isfile(os.path.join(search_dir, f))]
                                    md_files.extend(files)
                                except:
                                    pass
                        
                        md_files = sorted(list(set(md_files)))  # Remove duplicates
                        if md_files:
                            md_list = '\n'.join([f"- {f}" for f in md_files])
                            help_text = f"**{md_filename} not found.**\n\nAvailable markdown files:\n\n{md_list}\n\nUsage: `/read filename.md` (use exact filename from list above)"
                        else:
                            help_text = f"**{md_filename} not found.**\n\nNo markdown files found in: {script_dir}\n\nUsage: `/read filename.md` or `/show filename.md`\nExample: `/read FINANCIAL_USAGE.md`"
                else:
                    help_text = "Usage: `/read filename.md` or `/show filename.md`\nExample: `/read FINANCIAL_USAGE.md`\n\nUse `/docs` to see all available files."
                
                # Add to conversation history
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user_msg = {"role": "user", "content": user_message, "timestamp": timestamp}
                conversation_history.append(user_msg)
                conversation_history.append({"role": "assistant", "content": help_text, "timestamp": timestamp})
                st.session_state.conversation_histories[current_persona_name] = conversation_history
                # Display help immediately and rerun to show it
                st.markdown(help_text)
                st.rerun()
            
            elif command == '/docs':
                command_handled = True
                # List all available markdown files - try multiple directories
                try:
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                except NameError:
                    script_dir = os.getcwd()
                
                search_dirs = [script_dir, os.getcwd()]
                md_files = []
                for search_dir in search_dirs:
                    if os.path.exists(search_dir):
                        try:
                            files = [f for f in os.listdir(search_dir) if f.endswith('.md') and os.path.isfile(os.path.join(search_dir, f))]
                            md_files.extend(files)
                        except:
                            pass
                
                md_files = sorted(list(set(md_files)))  # Remove duplicates
                if md_files:
                    md_list = '\n'.join([f"- {f}" for f in md_files])
                    help_text = f"## Available Documentation Files\n\n{md_list}\n\nTo read a file, use:\n- `/read filename.md`\n- `/show filename.md`\n- Or just say: 'show me filename.md'"
                else:
                    help_text = f"No markdown documentation files found in: {script_dir} or {os.getcwd()}"
                
                # Add to conversation history
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user_msg = {"role": "user", "content": user_message, "timestamp": timestamp}
                conversation_history.append(user_msg)
                conversation_history.append({"role": "assistant", "content": help_text, "timestamp": timestamp})
                st.session_state.conversation_histories[current_persona_name] = conversation_history
                # Display help immediately and rerun to show it
                st.markdown(help_text)
                st.rerun()
            
            else:
                # Unknown command - show error but don't break
                st.warning(f"⚠️ Unknown command: {command}. Type `/help` for available commands.")
                # Continue with normal processing (remove the command part)
                user_message = command_args if command_args else ""
        
        # Normal message processing (only if command wasn't handled)
        if not command_handled:
            # Get contextual spinner message
            spinner_message = get_spinner_message(current_persona_name, agent.model_name)
            with st.spinner(spinner_message):
                # Handle uploaded files
                media_files = []
                temp_file_paths = []
                
                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        # Determine media type
                        file_ext = uploaded_file.name.split('.')[-1].lower()
                        if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                            media_type = "image"
                        elif file_ext in ['mp3', 'wav', 'ogg', 'm4a']:
                            media_type = "audio"
                        else:
                            continue
                        
                        # Save to temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name
                            temp_file_paths.append(tmp_path)
                            
                            media_files.append({
                                "type": media_type,
                                "path": tmp_path,
                                "description": f"User uploaded {media_type}: {uploaded_file.name}"
                            })
                
                # User message already set above (or use default)
                if not user_message:
                    user_message = user_input if user_input else "User shared media"
                
                # Prepare agent config with media
                agent_config = {}
                if media_files:
                    agent_config["media_files"] = media_files
                
                # Initialize result to None (will be set by agent.chat() if model is called)
                result = None
                response = ""  # Initialize response
                
                # Check for simple questions that can be answered without calling the model
                simple_question_handled = False
                user_message_lower = user_message.lower().strip()
                
                # Time/Date questions
                if any(phrase in user_message_lower for phrase in [
                    "what time", "what's the time", "current time", "time now", "what time is it",
                    "what date", "what's the date", "current date", "date today", "what date is it", "what day is it"
                ]):
                    import datetime
                    now = datetime.datetime.now()
                    if "time" in user_message_lower:
                        time_str = now.strftime("%I:%M %p")
                        response = f"It's currently {time_str}."
                    elif "date" in user_message_lower or "day" in user_message_lower:
                        date_str = now.strftime("%A, %B %d, %Y")
                        response = f"Today is {date_str}."
                    else:
                        datetime_str = now.strftime("%A, %B %d, %Y at %I:%M %p")
                        response = f"It's {datetime_str}."
                    simple_question_handled = True
                    # Set result to empty dict so later code doesn't fail
                    result = {"response": response}
                
                # Check if user is asking to see COMMANDS.md (specific handling)
                if not simple_question_handled and any(phrase in user_message_lower for phrase in [
                    "show me commands.md", "show commands.md", "show me the commands.md",
                    "display commands.md", "read commands.md", "open commands.md",
                    "show commands", "show me commands", "what commands", "list commands"
                ]):
                    commands_file = "COMMANDS.md"
                    if os.path.exists(commands_file):
                        try:
                            with open(commands_file, 'r', encoding='utf-8') as f:
                                commands_content = f.read()
                            response = f"Here's the COMMANDS.md file:\n\n{commands_content}"
                        except Exception as e:
                            response = f"I tried to read COMMANDS.md but got an error: {str(e)}"
                    else:
                        response = "COMMANDS.md file not found. You can use `/help` to see available commands."
                    simple_question_handled = True
                    # Set result to empty dict so later code doesn't fail
                    if result is None:
                        result = {"response": response}
                
                # Check if user is asking to read any markdown file
                if not simple_question_handled:
                    # Look for patterns like "show me X.md", "read X.md", "open X.md", "show X.md"
                    md_file_patterns = [
                        r'show\s+me\s+([a-zA-Z0-9_\-]+\.md)',
                        r'read\s+([a-zA-Z0-9_\-]+\.md)',
                        r'open\s+([a-zA-Z0-9_\-]+\.md)',
                        r'show\s+([a-zA-Z0-9_\-]+\.md)',
                        r'display\s+([a-zA-Z0-9_\-]+\.md)',
                        r'view\s+([a-zA-Z0-9_\-]+\.md)',
                        r'([a-zA-Z0-9_\-]+\.md)',  # Just the filename
                    ]
                    
                    import re
                    md_filename = None
                    for pattern in md_file_patterns:
                        match = re.search(pattern, user_message_lower)
                        if match:
                            md_filename = match.group(1)
                            # Make sure it ends with .md
                            if not md_filename.endswith('.md'):
                                md_filename = None
                                continue
                            break
                    
                    if md_filename:
                        # Check if file exists in current directory
                        if os.path.exists(md_filename):
                            try:
                                with open(md_filename, 'r', encoding='utf-8') as f:
                                    md_content = f.read()
                                response = f"Here's the {md_filename} file:\n\n{md_content}"
                                simple_question_handled = True
                                if result is None:
                                    result = {"response": response}
                            except Exception as e:
                                response = f"I tried to read {md_filename} but got an error: {str(e)}"
                                simple_question_handled = True
                                if result is None:
                                    result = {"response": response}
                        else:
                            # List available markdown files
                            md_files = [f for f in os.listdir('.') if f.endswith('.md') and os.path.isfile(f)]
                            if md_files:
                                md_list = '\n'.join([f"- {f}" for f in sorted(md_files)])
                                response = f"{md_filename} not found. Available markdown files:\n\n{md_list}\n\nTry: 'show me [filename].md'"
                            else:
                                response = f"{md_filename} not found. No markdown files available in the current directory."
                            simple_question_handled = True
                            if result is None:
                                result = {"response": response}
                
                if not simple_question_handled:
                    # Get response from agent (using current persona's thread_id)
                    try:
                        result = agent.chat(user_message, config=agent_config, thread_id=thread_id)
                        response = result.get("response", "")
                        
                        # Filter out JSON structures from response (common issue with some models)
                        if response:
                            response_stripped = response.strip()
                            
                            # Pattern 1: Code blocks with JSON
                            if response_stripped.startswith("```json") or response_stripped.startswith("```"):
                                json_block_pattern = r'```json.*?```|```.*?```'
                                cleaned = re.sub(json_block_pattern, '', response, flags=re.DOTALL).strip()
                                if cleaned:
                                    response = cleaned
                                else:
                                    # Try to extract content from JSON
                                    content_match = re.search(r'"content":\s*"([^"]+)"', response, re.DOTALL)
                                    if content_match:
                                        response = content_match.group(1)
                                    else:
                                        text_match = re.search(r'"text":\s*"([^"]+)"', response, re.DOTALL)
                                        if text_match:
                                            response = text_match.group(1)
                            
                            # Pattern 2: JSON object at start (common with conversation_log, update_to_cjs_json, etc.)
                            if response_stripped.startswith("{") and any(keyword in response_stripped for keyword in [
                                '"conversation_log"', '"update_to_cjs_json"', '"new_conversation_log"', 
                                '"isekai_adventures"', '"follow_up_topics"', '"newly_learned"'
                            ]):
                                # Try to extract meaningful text from JSON
                                # Look for quoted strings that are actual responses (not keys)
                                text_matches = re.findall(r'"(?:content|text|summary|response|message|advice|reflection)":\s*"([^"]+)"', response, re.DOTALL)
                                if text_matches:
                                    # Use the longest meaningful text
                                    response = max(text_matches, key=len)
                                else:
                                    # Look for any long quoted strings (likely actual content)
                                    all_quoted = re.findall(r'"([^"]{30,})"', response)
                                    if all_quoted:
                                        # Filter out keys and use content-like strings
                                        filtered = [q for q in all_quoted if not q.startswith(('conversation', 'update', 'isekai', 'follow'))]
                                        if filtered:
                                            response = max(filtered, key=len)
                                        else:
                                            response = max(all_quoted, key=len)
                                    else:
                                        # Last resort: remove JSON structure entirely
                                        response = re.sub(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', '', response, flags=re.DOTALL).strip()
                            
                            # Pattern 3: JSON-like structures in middle (clean them out)
                            if '"conversation_log"' in response or '"update_to_cjs_json"' in response:
                                # Remove JSON structures but keep surrounding text
                                json_pattern = r'\{[^{}]*"(?:conversation_log|update_to_cjs_json|new_conversation_log|isekai_adventures|follow_up_topics)"[^{}]*\}'
                                response = re.sub(json_pattern, '', response, flags=re.DOTALL)
                                # Clean up any remaining JSON artifacts
                                response = re.sub(r'\},\s*"', '', response)
                                response = re.sub(r'"\s*:\s*\{', '', response)
                            
                            # Pattern 4: Multiple JSON objects - extract the actual response text
                            if response.count('{') > 1:
                                # Try to find text that looks like a natural response
                                # Look for sentences that don't contain JSON structure keywords
                                sentences = response.split('.')
                                natural_sentences = []
                                for sentence in sentences:
                                    if not any(keyword in sentence for keyword in [
                                        'conversation_log', 'update_to_cjs_json', 'isekai_adventures',
                                        'follow_up_topics', 'newly_learned', '{"', '"}', '":'
                                    ]):
                                        natural_sentences.append(sentence.strip())
                                
                                if natural_sentences:
                                    response = '. '.join(natural_sentences).strip()
                                    if not response.endswith('.'):
                                        response += '.'
                            
                            # Final cleanup: remove any remaining JSON artifacts
                            response = re.sub(r'\s*\{[^}]*\}\s*', ' ', response)
                            response = re.sub(r'\s*\[[^\]]*\]\s*', ' ', response)
                            response = re.sub(r'\s+', ' ', response).strip()
                            
                            # Pattern 5: Catch JSON fragments like "json }" or "} json" or just "}"
                            json_fragments = [r'\bjson\s*\}', r'\}\s*json', r'^\s*\}\s*$', r'^\s*json\s*$', r'\}\s*$', r'^\s*json']
                            for fragment_pattern in json_fragments:
                                response = re.sub(fragment_pattern, '', response, flags=re.IGNORECASE).strip()
                            
                            # Pattern 6: Remove standalone JSON keywords
                            response = re.sub(r'\b(json|JSON)\b', '', response).strip()
                            response = re.sub(r'^\s*[\{\}\[\]]+\s*$', '', response).strip()
                            
                            # If response is too short or looks like JSON keys, try one more extraction
                            if len(response) < 50 or response.count('"') > response.count(' '):
                                # Last attempt: find text after ":" that's quoted
                                final_match = re.search(r':\s*"([^"]{50,})"', response)
                                if final_match:
                                    response = final_match.group(1)
                            
                            # Final safety check: if response is just JSON fragments, try to get previous response or generate error
                            if len(response.strip()) < 10 or response.strip().lower() in ['json', '}', '{', 'json }', '} json']:
                                # Response is too corrupted, try to extract from original
                                # Look for any sentence that doesn't contain JSON keywords
                                sentences = result.get("response", "").split('.')
                                natural_sentences = [s.strip() for s in sentences if s.strip() and 
                                                    not any(json_word in s.lower() for json_word in ['json', '{', '}', 'conversation_log', 'update_to_cjs'])]
                                if natural_sentences:
                                    response = '. '.join(natural_sentences[:3]).strip()
                                    if not response.endswith('.'):
                                        response += '.'
                                else:
                                    # Last resort: return a helpful message
                                    response = "I'm having trouble formatting my response properly. Could you ask that again?"
                        
                        # Show log file location if logging is enabled
                        if result:
                            log_file = result.get("log_file")
                            if log_file and os.path.exists(log_file):
                                # Show in sidebar or as info message
                                st.sidebar.caption(f"📝 Log: {os.path.basename(log_file)}")
                        
                        # Check if response is empty
                        if not response or response.strip() == "":
                            response = (
                                "I received your message but didn't get a response from the model. "
                                "This might indicate:\n"
                                "1. The model is not loaded (try: ollama pull llama3.2:3b)\n"
                                "2. Ollama is not running (try: ollama serve)\n"
                                "3. The model name in config.json is incorrect\n\n"
                                f"Current model: {CONFIG.get('model_name', 'unknown')}"
                            )
                            st.error("⚠️ Empty response received from agent")
                    except Exception as e:
                        response = f"Error calling agent: {str(e)}"
                        st.error(f"❌ Error: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                        # Ensure result is set even on error
                        if result is None:
                            result = {"response": response}
                
                # Store in conversation history with media (for current persona)
                # Note: Media files are saved to permanent storage by the agent's memory system
                # The display code will look up permanent paths from memory if temp files are missing
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                user_msg = {"role": "user", "content": user_message, "timestamp": timestamp}
                if media_files:
                    user_msg["media"] = media_files
                conversation_history.append(user_msg)
                
                assistant_msg = {"role": "assistant", "content": response, "timestamp": timestamp}
                # Add generated image if present (safely check result)
                if result is not None and isinstance(result, dict) and result.get("generated_image"):
                    assistant_msg["generated_image"] = result["generated_image"]
                conversation_history.append(assistant_msg)
                # Update session state with modified conversation history
                st.session_state.conversation_histories[current_persona_name] = conversation_history
                
                # Rerun to show the response immediately
                st.rerun()
                
                # Auto-create tool files if Tool Builder persona provided tool code
                if current_persona_name == "Tool Builder" or "Tool Builder" in current_persona_name:
                    try:
                        from tool_creator import create_tool_from_response
                        success, message = create_tool_from_response(response)
                        if success:
                            st.success(message)
                            st.info("🔄 Please restart the MCP server to use the new tool: `python3 local_mcp_server.py`")
                        elif "Could not extract" not in message:
                            # Only show if we tried but failed (not if we couldn't detect tool code)
                            st.warning(f"⚠️ Tool creation attempted but had issues: {message}")
                    except ImportError:
                        # tool_creator module not available - that's okay
                        pass
                    except Exception as e:
                        # Don't break the chat if tool creation fails
                        st.warning(f"⚠️ Tool creation error: {str(e)}")
                
                # Clean up temp files after storing to memory
                # The display code will retrieve permanent paths from memory when needed
                for tmp_path in temp_file_paths:
                    try:
                        # File is now stored in memory system, can delete temp
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                    except:
                        pass
            
            # Show proactive suggestions if any
            if result is not None and isinstance(result, dict) and result.get("should_proact") and result.get("proactivity_suggestions"):
                st.info("💡 " + result["proactivity_suggestions"][0])
            
            st.rerun()

elif page == "📊 Relationship":
    st.title("📊 Our Relationship")
    
    relationship_summary = memory.get_relationship_summary()
    personality_state = personality.get_current_personality()
    
    # Relationship overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Interactions", relationship_summary["total_interactions"])
    with col2:
        st.metric("Preferences Learned", relationship_summary["preferences_learned"])
    with col3:
        st.metric("Milestones", len(relationship_summary["milestones"]))
    with col4:
        # Note: Emotional patterns removed - this is a business tool
        pass
    
    st.markdown("---")
    
    # Personality traits visualization
    st.subheader("Mo11y's Personality Evolution")
    traits_data = []
    for trait_name, trait_info in personality_state["traits"].items():
        traits_data.append({
            "Trait": trait_name.title(),
            "Value": trait_info["value"],
            "Trend": trait_info["trend"]
        })
    
    if traits_data:
        df_traits = pd.DataFrame(traits_data)
        fig = px.bar(
            df_traits, 
            x="Trait", 
            y="Value",
            color="Trend",
            color_continuous_scale="RdYlGn",
            title="Current Personality Traits"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Milestones
    st.subheader("💝 Relationship Milestones")
    milestones = relationship_summary.get("milestones", [])
    if milestones:
        for milestone in milestones[:10]:  # Show last 10
            st.markdown(f"""
            <div class="milestone-card">
                <strong>{milestone['type'].title()}</strong><br>
                {milestone['description']}<br>
                <small>{milestone['timestamp']}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No milestones yet. Keep chatting to build our relationship! 💝")
    
    # Note: Emotional patterns section removed - this is a business tool
    
    # Timeline visualizations
    st.subheader("📈 Interaction Timeline")
    timeline_fig = timeline.create_interaction_timeline(days_back=90)
    st.plotly_chart(timeline_fig, use_container_width=True)
    
    # Sentiment heatmap
    st.subheader("🔥 Sentiment Heatmap")
    heatmap_fig = timeline.create_sentiment_heatmap(days_back=90)
    st.plotly_chart(heatmap_fig, use_container_width=True)
    
    # Milestone timeline
    st.subheader("🎯 Milestone Timeline")
    milestone_fig = timeline.create_milestone_timeline()
    st.plotly_chart(milestone_fig, use_container_width=True)
    
    # Personality radar
    st.subheader("🎭 Personality Radar")
    radar_fig = timeline.create_personality_radar(personality_state["traits"])
    st.plotly_chart(radar_fig, use_container_width=True)

elif page == "🧠 Memories":
    st.title("🧠 Memory Vault")
    
    # Memory search and filters
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("Search memories", placeholder="Enter keywords...")
    with col2:
        days_back = st.selectbox("Timeframe", [7, 30, 90, 365, "All"], index=1)
    
    # Retrieve memories
    days_value = days_back if isinstance(days_back, int) else None
    memories = memory.recall_episodic(
        limit=50,
        min_importance=0.0,
        days_back=days_value
    )
    
    # Filter by search query
    if search_query:
        query_lower = search_query.lower()
        memories = [m for m in memories if query_lower in m["content"].lower()]
    
    st.metric("Memories Found", len(memories))
    
    # Display memories with media
    for mem in memories[:20]:  # Show first 20
        importance_stars = "⭐" * int(mem["importance_score"] * 5)
        
        # Get associated media
        media_items = memory.recall_media(memory_id=mem['id'])
        
        with st.expander(f"📝 {mem['timestamp'][:10]} {importance_stars}", expanded=False):
            st.markdown(f"**Content:** {mem['content']}")
            st.markdown(f"**Tags:** {', '.join(mem.get('tags', [])[:3])}")
            st.markdown(f"**Importance:** {mem['importance_score']:.2f}")
            
            # Display media if present
            if media_items:
                st.markdown("**Media:**")
                for media in media_items:
                    if media['media_type'] == 'image':
                        if os.path.exists(media['file_path']):
                            st.image(media['file_path'], caption=media.get('description', ''), width=400)
                        elif media.get('thumbnail_path') and os.path.exists(media['thumbnail_path']):
                            st.image(media['thumbnail_path'], caption=media.get('description', ''), width=200)
                    elif media['media_type'] == 'audio':
                        if os.path.exists(media['file_path']):
                            st.audio(media['file_path'])
                            if media.get('transcription'):
                                st.caption(f"Transcription: {media['transcription']}")
                    st.caption(f"Type: {media['media_type']} | Size: {media.get('file_size', 0)} bytes")
    
    if not memories:
        st.info("No memories found. Start chatting to create memories! 💝")
    
    # Memory consolidation
    st.markdown("---")
    if st.button("🔄 Consolidate Old Memories"):
        with st.spinner("Consolidating memories..."):
            memory.consolidate_memories(days_threshold=30)
        st.success("Memories consolidated!")

elif page == "⚙️ Settings":
    st.title("⚙️ Settings")
    
    # Conversation Logging
    st.subheader("📝 Conversation Logging")
    if agent.logger:
        log_file = agent.logger.get_log_file_path()
        summary_file = agent.logger.get_summary_file_path()
        
        st.success("✅ Conversation logging is enabled")
        st.write(f"**Full log file:** `{log_file}`")
        st.write(f"**Summary file:** `{summary_file}`")
        st.caption(f"Logging {agent.logger.conversation_count} exchanges so far")
        
        # Show log file location
        if os.path.exists(log_file):
            log_size = os.path.getsize(log_file) / 1024  # KB
            st.info(f"📄 Log file size: {log_size:.1f} KB")
            
            # Option to view last few exchanges
            if st.button("📖 View Last 5 Exchanges"):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract last 5 exchanges
                        exchanges = content.split("EXCHANGE #")
                        if len(exchanges) > 1:
                            last_exchanges = exchanges[-6:]  # Last 5 + header
                            st.text_area("Last 5 Exchanges", "\n".join(last_exchanges), height=400)
                        else:
                            st.info("No exchanges logged yet")
                except Exception as e:
                    st.error(f"Error reading log file: {e}")
        
        if os.path.exists(summary_file):
            summary_size = os.path.getsize(summary_file) / 1024  # KB
            st.info(f"📄 Summary file size: {summary_size:.1f} KB")
            
            # Option to download log file
            if st.button("💾 Download Log File"):
                try:
                    with open(log_file, 'rb') as f:
                        st.download_button(
                            label="Download Full Log",
                            data=f.read(),
                            file_name=os.path.basename(log_file),
                            mime="text/plain"
                        )
                except Exception as e:
                    st.error(f"Error reading log file: {e}")
        
        st.markdown("---")
        st.caption("💡 Tip: After ~30 exchanges, review the log file to see what data sources were used. See CONVERSATION_LOGGING.md for details.")
    else:
        st.info("Conversation logging is disabled. Enable it when creating the agent.")
    
    st.markdown("---")
    
    # Personality settings
    st.subheader("Personality Configuration")
    personality_state = personality.get_current_personality()
    
    for trait_name, trait_info in personality_state["traits"].items():
        current_value = trait_info["value"]
        st.slider(
            trait_name.title(),
            min_value=0.0,
            max_value=1.0,
            value=current_value,
            disabled=True,  # Auto-adjusted by interactions
            help="This trait evolves based on our interactions"
        )
    
    st.info("💡 Personality traits evolve automatically based on our interactions!")
    
    # External API Status
    if agent.external_apis:
        st.subheader("🔌 External API Status")
        api_status = agent.external_apis.get_api_status()
        
        st.write(f"**Registered APIs:** {len(api_status.get('registered_apis', []))}")
        st.write(f"**Enabled APIs:** {len(api_status.get('enabled_apis', []))}")
        
        if api_status.get('statistics'):
            st.write("**API Usage (Last 7 Days):**")
            stats_df = pd.DataFrame([
                {
                    'API': name,
                    'Calls': stats['call_count'],
                    'Avg Response Time (ms)': round(stats['avg_response_time_ms'], 2),
                    'Last Call': stats.get('last_call', 'Never')
                }
                for name, stats in api_status['statistics'].items()
            ])
            st.dataframe(stats_df, use_container_width=True)
        
        # API Configuration
        with st.expander("Configure External APIs"):
            st.info("Use the ExternalAPIManager in Python to register APIs. See MULTIMODAL_MCP_SETUP.md for details.")
    
    # MCP Integration Status & Tool Calling
    if agent.mcp_client:
        st.subheader("🔧 MCP Tools")
        
        try:
            server_info = agent.mcp_client.get_server_info()
            if server_info:
                st.success("✅ MCP Server Connected")
            
            # List available tools
            tools = agent.mcp_client.list_tools()
            if tools:
                st.write(f"**Available Tools:** {len(tools)}")
                
                # Quick Web Search Tool
                if any(tool['name'] == 'web_search' for tool in tools):
                    st.markdown("---")
                    st.subheader("🔍 Web Search")
                    with st.form("web_search_form"):
                        search_query = st.text_input("Search the web:", placeholder="Enter your search query...")
                        max_results = st.slider("Max results:", 1, 10, 5)
                        search_submitted = st.form_submit_button("🔍 Search", use_container_width=True)
                        
                        if search_submitted and search_query:
                            with st.spinner("Searching the web..."):
                                try:
                                    result = agent.mcp_client.call_tool(
                                        "web_search",
                                        {"query": search_query, "max_results": max_results}
                                    )
                                    if result and result.get("content"):
                                        search_content = result["content"][0].get("text", "")
                                        st.success("Search completed!")
                                        st.markdown(f"<div style='max-height: 400px; overflow-y: auto; padding: 10px; background-color: #f0f2f6; border-radius: 5px;'>{search_content}</div>", unsafe_allow_html=True)
                                        
                                        # Option to add to conversation
                                        if st.button("💬 Add to Conversation", key="add_search_to_chat"):
                                            # Add to current persona's conversation history
                                            if current_persona_name not in st.session_state.conversation_histories:
                                                st.session_state.conversation_histories[current_persona_name] = []
                                            st.session_state.conversation_histories[current_persona_name].append({
                                                "role": "assistant",
                                                "content": f"Web search results for '{search_query}':\n\n{search_content}"
                                            })
                                            st.rerun()
                                    else:
                                        st.error("No results found or error occurred")
                                except Exception as e:
                                    st.error(f"Search error: {str(e)}")
                
                # Other Tools Expander
                with st.expander("📋 View All Tools"):
                    for tool in tools:
                        tool_name = tool['name']
                        tool_desc = tool.get('description', 'No description')
                        
                        st.write(f"**{tool_name}**")
                        st.caption(tool_desc)
                        
                        # Show parameters if available
                        if 'inputSchema' in tool and 'properties' in tool['inputSchema']:
                            params = tool['inputSchema']['properties']
                            if params:
                                st.write("Parameters:")
                                for param_name, param_def in params.items():
                                    param_desc = param_def.get('description', '')
                                    param_type = param_def.get('type', 'string')
                                    st.write(f"  - `{param_name}` ({param_type}): {param_desc}")
                        
                        # Quick call button for simple tools
                        if tool_name != 'web_search':  # web_search has its own form above
                            with st.expander(f"🔧 Call {tool_name}", expanded=False):
                                tool_params = {}
                                if 'inputSchema' in tool and 'properties' in tool['inputSchema']:
                                    params = tool['inputSchema']['properties']
                                    for param_name, param_def in params.items():
                                        param_type = param_def.get('type', 'string')
                                        if param_type == 'integer':
                                            tool_params[param_name] = st.number_input(
                                                param_name,
                                                value=param_def.get('default', 0),
                                                key=f"tool_{tool_name}_{param_name}"
                                            )
                                        elif param_type == 'boolean':
                                            tool_params[param_name] = st.checkbox(
                                                param_name,
                                                value=param_def.get('default', False),
                                                key=f"tool_{tool_name}_{param_name}"
                                            )
                                        else:
                                            tool_params[param_name] = st.text_input(
                                                param_name,
                                                value=param_def.get('default', ''),
                                                placeholder=param_def.get('description', ''),
                                                key=f"tool_{tool_name}_{param_name}"
                                            )
                                
                                if st.button(f"Run {tool_name}", key=f"run_{tool_name}"):
                                    with st.spinner(f"Running {tool_name}..."):
                                        try:
                                            result = agent.mcp_client.call_tool(tool_name, tool_params)
                                            if result:
                                                if result.get("isError"):
                                                    st.error(f"Error: {result.get('content', [{}])[0].get('text', 'Unknown error')}")
                                                else:
                                                    result_text = result.get('content', [{}])[0].get('text', str(result))
                                                    st.success("Tool executed successfully!")
                                                    st.markdown(f"<div style='max-height: 300px; overflow-y: auto; padding: 10px; background-color: #f0f2f6; border-radius: 5px;'>{result_text}</div>", unsafe_allow_html=True)
                                            else:
                                                st.warning("Tool returned no result")
                                        except Exception as e:
                                            st.error(f"Error calling tool: {str(e)}")
                        
                        st.markdown("---")
            else:
                st.info("No MCP tools available")
        except Exception as e:
            st.warning(f"⚠️ MCP Server: {str(e)}")
    else:
        st.subheader("🔧 MCP Tools")
        st.info("MCP integration not enabled or MCP server not found.")
        st.caption("To enable: Start local MCP server with `python3 local_mcp_server.py` or set MCP_SERVER_URL in config.json")
    
    # Memory settings
    st.subheader("Memory Settings")
    
    # Media statistics
    media_stats = memory.recall_media(limit=1000)
    if media_stats:
        image_count = sum(1 for m in media_stats if m['media_type'] == 'image')
        audio_count = sum(1 for m in media_stats if m['media_type'] == 'audio')
        total_size = sum(m.get('file_size', 0) for m in media_stats)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Images Stored", image_count)
        with col2:
            st.metric("Audio Files", audio_count)
        with col3:
            st.metric("Total Media Size", f"{total_size / 1024 / 1024:.2f} MB")
    
    # Memory deletion with multi-step security
    st.markdown("---")
    st.subheader("🗑️ Delete Data")
    
    # Initialize session state for deletion process
    if "delete_step" not in st.session_state:
        st.session_state.delete_step = 0
    if "delete_include_personality" not in st.session_state:
        st.session_state.delete_include_personality = False
    if "delete_include_media" not in st.session_state:
        st.session_state.delete_include_media = True
    
    # Step 0: Initial button
    if st.session_state.delete_step == 0:
        st.warning("⚠️ **DANGER ZONE** - These actions cannot be undone!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear All Memories", use_container_width=True):
                st.session_state.delete_step = 1
                st.session_state.delete_type = "all_memories"
                st.rerun()
        
        with col2:
            if st.button("🧹 Clear Old Memories Only", use_container_width=True):
                st.session_state.delete_step = 1
                st.session_state.delete_type = "old_memories"
                st.rerun()
    
    # Step 1: Show what will be deleted
    elif st.session_state.delete_step == 1:
        st.error("⚠️ **WARNING: This will permanently delete data!**")
        
        if st.session_state.delete_type == "all_memories":
            st.markdown("### What will be deleted:")
            st.markdown("""
            **Memory Data:**
            - ✅ All conversations (episodic memories)
            - ✅ All facts about you (semantic memories)
            - ✅ All memories
            - ✅ All relationship milestones
            - ✅ All learned preferences
            - ✅ All conversation patterns
            - ✅ All memory associations
            - ✅ All media files (images, audio) - if enabled
            
            **Personality Data (optional):**
            - ⚠️ Evolved personality traits (will reset to defaults)
            - ⚠️ Communication style preferences
            - ⚠️ Relationship dynamics
            
            **What will NOT be deleted:**
            - ✅ External API configurations (calendar, weather, etc.)
            - ✅ API cache and call history
            - ✅ journal.json file
            """)
            
            st.session_state.delete_include_personality = st.checkbox(
                "Also reset personality data? (uncheck to keep personality evolution)",
                value=False
            )
            st.session_state.delete_include_media = st.checkbox(
                "Also delete media files from disk? (images, audio)",
                value=True
            )
        
        elif st.session_state.delete_type == "old_memories":
            st.markdown("### What will be deleted:")
            st.markdown("""
            **Old, Low-Importance Memories Only:**
            - ✅ Conversations older than 90 days with low importance (< 0.3)
            - ✅ Related memories
            - ✅ Related semantic memories
            - ✅ Related media files
            
            **What will be kept:**
            - ✅ Recent conversations
            - ✅ Important memories (importance > 0.3)
            - ✅ All relationship milestones
            - ✅ All preferences
            - ✅ All personality data
            """)
            
            days_old = st.slider("Delete memories older than (days):", 30, 365, 90)
            st.session_state.delete_days_old = days_old
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.delete_step = 0
                st.rerun()
        with col2:
            if st.button("⚠️ Continue to Confirmation", use_container_width=True):
                st.session_state.delete_step = 2
                st.rerun()
    
    # Step 2: Type confirmation
    elif st.session_state.delete_step == 2:
        st.error("⚠️ **FINAL WARNING**")
        
        if st.session_state.delete_type == "all_memories":
            confirmation_text = "DELETE ALL MEMORIES"
        else:
            confirmation_text = "DELETE OLD MEMORIES"
        
        st.markdown(f"### Type `{confirmation_text}` to confirm:")
        confirmation_input = st.text_input(
            "Confirmation:",
            key="delete_confirmation",
            placeholder=f"Type: {confirmation_text}"
        )
        
        # Get current counts for display
        if st.session_state.delete_type == "all_memories":
            relationship_summary = memory.get_relationship_summary()
            total_memories = relationship_summary.get("total_interactions", 0)
            st.info(f"📊 **Current Stats:** {total_memories} total interactions will be deleted")
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("❌ Go Back", use_container_width=True):
                st.session_state.delete_step = 1
                st.rerun()
        with col2:
            if confirmation_input == confirmation_text:
                if st.button("🗑️ **PERMANENTLY DELETE**", use_container_width=True, type="primary"):
                    st.session_state.delete_step = 3
                    st.rerun()
            else:
                st.button("🗑️ **PERMANENTLY DELETE**", use_container_width=True, disabled=True)
                st.caption(f"Type '{confirmation_text}' to enable deletion")
    
    # Step 3: Execute deletion
    elif st.session_state.delete_step == 3:
        st.error("🗑️ **DELETING DATA...**")
        
        with st.spinner("Deleting data... This may take a moment."):
            try:
                if st.session_state.delete_type == "all_memories":
                    # Delete memories
                    counts = memory.clear_all_memories(include_media=st.session_state.delete_include_media)
                    
                    # Delete personality if requested
                    personality_counts = {}
                    if st.session_state.delete_include_personality:
                        personality_counts = personality.clear_personality_data()
                    
                    st.success("✅ **Deletion Complete!**")
                    st.markdown("### Deleted:")
                    st.json({
                        "Memories": counts,
                        "Personality": personality_counts if personality_counts else "Kept (not deleted)"
                    })
                    
                elif st.session_state.delete_type == "old_memories":
                    counts = memory.clear_old_memories(
                        days_old=st.session_state.delete_days_old,
                        min_importance=0.3
                    )
                    
                    st.success("✅ **Cleanup Complete!**")
                    st.markdown("### Deleted:")
                    st.json(counts)
                
                # Reset deletion state
                st.session_state.delete_step = 0
                st.info("🔄 **Please refresh the page to see updated stats.**")
                
            except Exception as e:
                st.error(f"❌ **Error during deletion:** {str(e)}")
                import traceback
                st.code(traceback.format_exc())
                st.session_state.delete_step = 0
    
    # Export/Import
    st.subheader("Data Management")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Export Memories"):
            # Export functionality
            st.info("Export feature coming soon!")
    with col2:
        if st.button("📤 Import Memories"):
            uploaded_file = st.file_uploader("Choose a file", type="json")
            if uploaded_file:
                st.info("Import feature coming soon!")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #667eea;'>💝 Mo11y - Growing with you, every day 💝</div>",
    unsafe_allow_html=True
)
