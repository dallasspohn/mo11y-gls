#!/usr/bin/env python3
"""
Check if database timestamp updates after agent conversation
"""

import os
import json
import time
from datetime import datetime

# Get database path from config
config_path = "config.json"
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)
        db_path = config.get("db_path", "./SPOHNZ.db")
else:
    db_path = "./SPOHNZ.db"

print("="*70)
print("DATABASE TIMESTAMP CHECK")
print("="*70)
print(f"Database: {db_path}")
print()

# Get initial timestamp
if os.path.exists(db_path):
    initial_mtime = os.path.getmtime(db_path)
    initial_time_str = datetime.fromtimestamp(initial_mtime).strftime("%Y-%m-%d %H:%M:%S")
    print(f"Initial timestamp: {initial_time_str}")
    print(f"Initial mtime: {initial_mtime}")
else:
    print(f"❌ Database file not found: {db_path}")
    exit(1)

print("\n" + "-"*70)
print("Testing direct database write...")
print("-"*70)

# Test direct write
import sqlite3
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("INSERT INTO episodic_memories (content, importance_score) VALUES (?, ?)", 
               (f"Timestamp test at {datetime.now()}", 0.5))
conn.commit()
conn.close()

# Wait a moment for filesystem to update
time.sleep(0.2)

# Check new timestamp
new_mtime = os.path.getmtime(db_path)
new_time_str = datetime.fromtimestamp(new_mtime).strftime("%Y-%m-%d %H:%M:%S")
print(f"After direct write:")
print(f"  New timestamp: {new_time_str}")
print(f"  New mtime: {new_mtime}")
print(f"  Timestamp updated: {'✅ YES' if new_mtime > initial_mtime else '❌ NO'}")

print("\n" + "-"*70)
print("Testing EnhancedMemory.remember_episodic()...")
print("-"*70)

# Test using EnhancedMemory
from enhanced_memory import EnhancedMemory
memory = EnhancedMemory(db_path)

# Get timestamp before
before_mtime = os.path.getmtime(db_path)
before_time_str = datetime.fromtimestamp(before_mtime).strftime("%Y-%m-%d %H:%M:%S")
print(f"Before remember_episodic: {before_time_str}")

# Save memory
memory_id = memory.remember_episodic(
    content=f"EnhancedMemory test at {datetime.now()}",
    importance=0.7
)

# Wait for filesystem
time.sleep(0.2)

# Check timestamp after
after_mtime = os.path.getmtime(db_path)
after_time_str = datetime.fromtimestamp(after_mtime).strftime("%Y-%m-%d %H:%M:%S")
print(f"After remember_episodic: {after_time_str}")
print(f"Timestamp updated: {'✅ YES' if after_mtime > before_mtime else '❌ NO'}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"Current database timestamp: {datetime.fromtimestamp(os.path.getmtime(db_path)).strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Database file size: {os.path.getsize(db_path):,} bytes")

# Check if database appears in ls -lart
print("\n" + "-"*70)
print("Files sorted by modification time (ls -lart):")
print("-"*70)
import subprocess
result = subprocess.run(["ls", "-lart"], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(db_path)))
lines = result.stdout.strip().split('\n')
db_filename = os.path.basename(db_path)
for i, line in enumerate(lines):
    if db_filename in line:
        position = len(lines) - i
        print(f"✅ Database found at position {position} from bottom (out of {len(lines)} files)")
        print(f"   {line}")
        break
else:
    print(f"❌ Database not found in ls -lart output")

print("\n" + "="*70)
print("If database timestamp is NOT updating:")
print("="*70)
print("1. Check if agent is actually calling store_memory()")
print("2. Check if database connections are being closed properly")
print("3. Check if there are multiple database instances")
print("4. Check filesystem sync delays (use sync command)")
print("="*70)
