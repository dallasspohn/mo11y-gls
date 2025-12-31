#!/usr/bin/env python3
"""
Merge life-journal-main.json (year-based structure) with life-journal.json (flat structure)
Converts year-based data into the format expected by LifeJournal class
"""

import json
import os
from datetime import datetime
from collections import defaultdict

def merge_life_journals():
    # Paths
    main_journal_path = "../life-journal-main.json"
    current_journal_path = "life-journal.json"
    
    # Load both files
    print(f"Loading {main_journal_path}...")
    with open(main_journal_path, 'r', encoding='utf-8') as f:
        main_data = json.load(f)
    
    print(f"Loading {current_journal_path}...")
    if os.path.exists(current_journal_path):
        with open(current_journal_path, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
    else:
        current_data = {
            "subject": {
                "name": "Dallas Spohn",
                "age": 53,
                "location": "Crandall, TX 75114",
                "employer": "Red Hat",
                "birth_date": None,
                "birth_location": None
            },
            "timeline": [],
            "friends": [],
            "family": [],
            "locations": [],
            "education": [],
            "career": [],
            "relationships": [],
            "significant_events": [],
            "interests": [],
            "patterns": {
                "emotional_patterns": [],
                "decision_patterns": [],
                "communication_patterns": []
            }
        }
    
    # Update subject info from main journal if available
    if "personal_data" in main_data:
        personal = main_data["personal_data"]
        if personal.get("name"):
            current_data["subject"]["name"] = personal["name"]
    
    # Extract birth info from year 1972
    for year_data in main_data.get("years", []):
        if year_data.get("year") == 1972:
            for loc in year_data.get("locations", []):
                if "born" in loc.get("memories", "").lower():
                    current_data["subject"]["birth_location"] = f"{loc.get('city', '')}, {loc.get('country', '')}"
                    # Try to extract birth date from journal entries
                    for entry in year_data.get("journal_entries", []):
                        if "born" in entry.get("entry", "").lower():
                            date_str = entry.get("date", "")
                            if date_str:
                                current_data["subject"]["birth_date"] = date_str
                    break
    
    # Convert year-based data to flat structure
    print("Converting year-based data to flat structure...")
    
    # Process timeline entries (from journal_entries)
    timeline_entries = []
    for year_data in main_data.get("years", []):
        year = year_data.get("year")
        for entry in year_data.get("journal_entries", []):
            timeline_entries.append({
                "year": year,
                "content": entry.get("entry", ""),
                "context": {"date": entry.get("date", "")},
                "added_at": datetime.now().isoformat()
            })
    
    # Process friends
    friends_dict = {}
    for year_data in main_data.get("years", []):
        year = year_data.get("year")
        # Handle string friends
        for friend_str in year_data.get("friends", []):
            if isinstance(friend_str, str) and friend_str.strip():
                # Try to parse structured friend data
                if "," in friend_str:
                    parts = friend_str.split(",")
                    name = parts[0].strip()
                    if name and name.lower() not in ["no", ""]:
                        if name not in friends_dict:
                            friends_dict[name] = {
                                "name": name,
                                "met_at": f"Year {year}",
                                "relationship": "",
                                "memories": [],
                                "context": {"years": [year]},
                                "added_at": datetime.now().isoformat()
                            }
                        else:
                            if year not in friends_dict[name]["context"].get("years", []):
                                friends_dict[name]["context"]["years"].append(year)
        
        # Handle dict friends
        for friend_obj in year_data.get("friends", []):
            if isinstance(friend_obj, dict):
                name = friend_obj.get("name", "").strip()
                if name and name.lower() not in ["no", ""]:
                    if name not in friends_dict:
                        friends_dict[name] = {
                            "name": name,
                            "met_at": friend_obj.get("met_at", f"Year {year}"),
                            "relationship": friend_obj.get("relationship", ""),
                            "memories": [friend_obj.get("memories", "")] if friend_obj.get("memories") else [],
                            "context": {"years": [year]},
                            "added_at": datetime.now().isoformat()
                        }
                    else:
                        # Merge with existing
                        if friend_obj.get("met_at"):
                            friends_dict[name]["met_at"] = friend_obj["met_at"]
                        if friend_obj.get("relationship"):
                            friends_dict[name]["relationship"] = friend_obj["relationship"]
                        if friend_obj.get("memories"):
                            friends_dict[name]["memories"].append(friend_obj["memories"])
                        if year not in friends_dict[name]["context"].get("years", []):
                            friends_dict[name]["context"]["years"].append(year)
    
    # Process locations
    locations_dict = {}
    for year_data in main_data.get("years", []):
        year = year_data.get("year")
        for loc in year_data.get("locations", []):
            address = loc.get("address", "")
            city = loc.get("city", "")
            key = f"{city}_{address}"
            
            memories = loc.get("memories", "")
            if isinstance(memories, list):
                memories_list = memories
            elif isinstance(memories, str):
                memories_list = [memories] if memories else []
            else:
                memories_list = []
            
            if key not in locations_dict:
                locations_dict[key] = {
                    "address": address,
                    "city": city,
                    "state": None,
                    "country": loc.get("country", "USA"),
                    "years": [year],
                    "memories": memories_list,
                    "added_at": datetime.now().isoformat()
                }
            else:
                if year not in locations_dict[key]["years"]:
                    locations_dict[key]["years"].append(year)
                locations_dict[key]["memories"].extend(memories_list)
    
    # Process education
    education_list = []
    for year_data in main_data.get("years", []):
        year = year_data.get("year")
        for edu in year_data.get("education", []):
            if isinstance(edu, dict) and edu.get("institution"):
                education_list.append({
                    "institution": edu.get("institution", ""),
                    "role": edu.get("role", "Student"),
                    "years": [year],
                    "achievements": [edu.get("achievements", "")] if edu.get("achievements") else [],
                    "added_at": datetime.now().isoformat()
                })
    
    # Process interests/hobbies
    interests_list = []
    for year_data in main_data.get("years", []):
        year = year_data.get("year")
        for hobby in year_data.get("hobbies", []):
            if isinstance(hobby, dict):
                hobby_name = hobby.get("hobby", "")
                if isinstance(hobby_name, list):
                    hobby_name = ", ".join(hobby_name)
                if hobby_name:
                    interests_list.append({
                        "name": hobby_name,
                        "years": [year],
                        "duration": hobby.get("duration", ""),
                        "significance": hobby.get("significance", ""),
                        "added_at": datetime.now().isoformat()
                    })
    
    # Process family from personal_data
    family_list = []
    if "personal_data" in main_data and "family_members" in main_data["personal_data"]:
        for member in main_data["personal_data"]["family_members"]:
            family_list.append({
                "name": member.get("name", ""),
                "relationship": member.get("relationship", ""),
                "rag_file": member.get("rag_file", ""),
                "added_at": datetime.now().isoformat()
            })
    
    # Merge with existing data (avoid duplicates)
    print("Merging data...")
    
    # Merge timeline (append new entries)
    existing_timeline_content = {e.get("content", "")[:50] for e in current_data.get("timeline", [])}
    for entry in timeline_entries:
        if entry.get("content", "")[:50] not in existing_timeline_content:
            current_data["timeline"].append(entry)
    
    # Sort timeline by year
    current_data["timeline"].sort(key=lambda x: x.get("year") or 0)
    
    # Merge friends (update existing, add new)
    existing_friends = {f["name"].lower(): f for f in current_data.get("friends", [])}
    for friend in friends_dict.values():
        name_lower = friend["name"].lower()
        if name_lower in existing_friends:
            # Merge memories
            existing_friends[name_lower]["memories"].extend(friend.get("memories", []))
            if friend.get("met_at"):
                existing_friends[name_lower]["met_at"] = friend["met_at"]
            if friend.get("relationship"):
                existing_friends[name_lower]["relationship"] = friend["relationship"]
        else:
            current_data["friends"].append(friend)
    
    # Merge locations (update existing, add new)
    existing_locations = {(l.get("city", ""), l.get("address", "")): l 
                         for l in current_data.get("locations", [])}
    for loc in locations_dict.values():
        key = (loc["city"], loc["address"])
        if key in existing_locations:
            # Merge memories and years
            existing_locations[key]["memories"].extend(loc.get("memories", []))
            existing_locations[key]["years"] = list(set(existing_locations[key].get("years", []) + loc.get("years", [])))
        else:
            current_data["locations"].append(loc)
    
    # Merge education (append new)
    existing_edu = {(e.get("institution", ""), e.get("role", "")): e 
                   for e in current_data.get("education", [])}
    for edu in education_list:
        key = (edu["institution"], edu["role"])
        if key not in existing_edu:
            current_data["education"].append(edu)
    
    # Merge interests (append new)
    existing_interests = {i.get("name", "").lower(): i for i in current_data.get("interests", [])}
    for interest in interests_list:
        name_lower = interest["name"].lower()
        if name_lower not in existing_interests:
            current_data["interests"].append(interest)
    
    # Merge family (replace with main journal family data)
    if family_list:
        current_data["family"] = family_list
    
    # Update last_updated
    current_data["last_updated"] = datetime.now().isoformat()
    
    # Save merged journal
    print(f"Saving merged journal to {current_journal_path}...")
    with open(current_journal_path, 'w', encoding='utf-8') as f:
        json.dump(current_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nMerge complete!")
    print(f"  Timeline entries: {len(current_data['timeline'])}")
    print(f"  Friends: {len(current_data['friends'])}")
    print(f"  Locations: {len(current_data['locations'])}")
    print(f"  Education: {len(current_data['education'])}")
    print(f"  Interests: {len(current_data['interests'])}")
    print(f"  Family: {len(current_data['family'])}")

if __name__ == "__main__":
    merge_life_journals()
