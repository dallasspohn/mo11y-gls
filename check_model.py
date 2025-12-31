#!/usr/bin/env python3
"""
Quick diagnostic script to check model configuration and availability
Run this on your server to verify model setup
"""

import json
import os
from ollama import list as ollama_list

def main():
    print("=" * 60)
    print("Mo11y Model Configuration Checker")
    print("=" * 60)
    
    # Check config.json
    config_path = "config.json"
    if os.path.exists(config_path):
        print(f"\n✓ Found config.json")
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                model_name = config.get("model_name", "NOT SET")
                print(f"  Model name in config: {model_name}")
        except Exception as e:
            print(f"  ✗ Error reading config.json: {e}")
            model_name = None
    else:
        print(f"\n✗ config.json not found at {config_path}")
        model_name = None
    
    # Check available Ollama models
    print(f"\n{'=' * 60}")
    print("Available Ollama Models:")
    print("=" * 60)
    try:
        models = ollama_list()
        model_list = models.get("models", [])
        
        if not model_list:
            print("  ✗ No models found! Run: ollama pull <model-name>")
        else:
            print(f"  ✓ Found {len(model_list)} model(s):\n")
            for model in model_list:
                name = model.get("name", "unknown")
                size = model.get("size", 0)
                size_gb = size / (1024**3) if size else 0
                modified = model.get("modified_at", "unknown")
                
                # Highlight if it matches config
                match_indicator = " ← CONFIG" if model_name and name == model_name else ""
                print(f"    • {name:<30} ({size_gb:.2f} GB) {match_indicator}")
            
            # Check if configured model is available
            if model_name:
                print(f"\n{'=' * 60}")
                model_names = [m.get("name", "") for m in model_list]
                if model_name in model_names:
                    print(f"✓ SUCCESS: Model '{model_name}' is available!")
                else:
                    print(f"✗ ERROR: Model '{model_name}' NOT found in available models")
                    print(f"\n  To fix this, run:")
                    print(f"    ollama pull {model_name}")
                    print(f"\n  Or update config.json to use one of the available models above.")
                    
                    # Suggest similar models
                    model_base = model_name.split(':')[0].lower()
                    similar = [m for m in model_names if model_base in m.lower()]
                    if similar:
                        print(f"\n  Similar models found: {', '.join(similar)}")
    except Exception as e:
        print(f"  ✗ Error connecting to Ollama: {e}")
        print(f"    Make sure Ollama is running: ollama serve")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
