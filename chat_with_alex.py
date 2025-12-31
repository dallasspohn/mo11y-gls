#!/usr/bin/env python3
"""
Interactive chat script to converse with Alex Mercer
Run this to have a conversation with Alex directly from the command line
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mo11y_agent import create_mo11y_agent
import json

def main():
    print("=" * 80)
    print("💬 Chat with Alex Mercer")
    print("=" * 80)
    print("Type your messages below. Type '/exit' or '/quit' to end the conversation.")
    print("Type '/clear' to clear the conversation history.")
    print()
    
    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except:
        config = {}
    
    # Create agent with Alex persona
    sona_path = os.path.join("sonas", "alex-mercer.json")
    if not os.path.exists(sona_path):
        print(f"Error: Could not find {sona_path}")
        return
    
    print("Initializing Alex Mercer...")
    agent = create_mo11y_agent(
        model_name=config.get("model_name", "deepseek-r1:latest"),
        sona_path=sona_path,
        enable_mcp=True,
        enable_external_apis=True,
        suppress_thinking=True,
        enable_logging=True
    )
    
    print("✅ Alex is ready!")
    print()
    
    conversation_count = 0
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ['/exit', '/quit', '/q']:
                print("\n👋 Goodbye! Alex enjoyed chatting with you.")
                break
            
            if user_input.lower() == '/clear':
                # Clear conversation history by creating new thread
                agent.thread_id = f"thread_alex_mercer_{conversation_count}"
                print("🗑️  Conversation history cleared.")
                continue
            
            # Get response from agent
            print("Alex: ", end="", flush=True)
            
            result = agent.chat(
                user_input,
                thread_id=f"thread_alex_mercer_interactive"
            )
            
            response = result.get("response", "")
            
            # Display response
            print(response)
            
            # Show image if generated
            if result.get("generated_image"):
                image_path = result["generated_image"]
                print(f"\n🖼️  Image generated: {image_path}")
            
            conversation_count += 1
            print()  # Blank line for readability
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print()

if __name__ == "__main__":
    main()
