"""
Journal System for Mo11y
Maintains comprehensive business and biographical data
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from enhanced_memory import EnhancedMemory

# Optional spaCy integration (best-effort, optional dependency)
SPACY_AVAILABLE = False
nlp = None

try:
    import spacy  # type: ignore
    # Try to load a commonly used small English model. If it's not installed,
    # loading will raise an exception and we will fallback gracefully.
    try:
        nlp = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
    except Exception:
        # If the model isn't installed, don't crash — spaCy is optional
        nlp = None
        SPACY_AVAILABLE = False
except Exception:
    SPACY_AVAILABLE = False
    nlp = None


class Journal:
    """
    Maintains journal.json with business and biographical data
    Formatted for optimal recall and pattern recognition
    """

    def __init__(self, journal_path: str = "journal.json", memory: Optional[EnhancedMemory] = None):
        self.journal_path = journal_path
        self.memory = memory
        self.journal = self._load_journal()

    def _load_journal(self) -> Dict:
        """Load existing journal or create new structure"""
        if os.path.exists(self.journal_path):
            try:
                with open(self.journal_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return self._create_empty_journal()
        return self._create_empty_journal()

    def _create_empty_journal(self) -> Dict:
        """Create empty journal structure"""
        return {
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
                "decision_patterns": [],
                "communication_patterns": []
            },
            "last_updated": datetime.now().isoformat()
        }

    def save_journal(self):
        """Save journal to file"""
        self.journal["last_updated"] = datetime.now().isoformat()
        with open(self.journal_path, 'w', encoding='utf-8') as f:
            json.dump(self.journal, f, indent=2, ensure_ascii=False)

    def add_timeline_entry(self, year: Optional[int], content: str, context: Dict = None):
        """Add entry to timeline (saves to journal.json only)"""
        entry = {
            "year": year,
            "content": content,
            "context": context or {},
            "added_at": datetime.now().isoformat()
        }
        self.journal["timeline"].append(entry)
        self.journal["timeline"].sort(key=lambda x: x.get("year") or 0)
        self.save_journal()
        
        # Note: Journal entries are now stored only in journal.json for simplicity
        # This makes them easier to track, edit, and backup over time

    def add_friend(self, name: str, met_at: str = None, relationship: str = None,
                   memories: List[str] = None, context: Dict = None):
        """Add or update friend information"""
        # Check if friend already exists
        existing = next((f for f in self.journal["friends"] if f["name"].lower() == name.lower()), None)

        if existing:
            # Update existing
            if met_at:
                existing["met_at"] = met_at
            if relationship:
                existing["relationship"] = relationship
            if memories:
                existing["memories"] = existing.get("memories", []) + memories
            if context:
                existing["context"] = {**existing.get("context", {}), **context}
        else:
            # Add new friend
            self.journal["friends"].append({
                "name": name,
                "met_at": met_at,
                "relationship": relationship,
                "memories": memories or [],
                "context": context or {},
                "added_at": datetime.now().isoformat()
            })

        self.save_journal()

    def add_location(self, address: str, city: str, state: str = None,
                     country: str = "USA", years: List[int] = None, memories: List[str] = None):
        """Add or update location information"""
        location_key = f"{city}, {state or country}"
        existing = next((l for l in self.journal["locations"]
                        if l.get("city") == city and l.get("address") == address), None)

        if existing:
            if years:
                existing["years"] = list(set(existing.get("years", []) + years))
            if memories:
                existing["memories"] = existing.get("memories", []) + memories
        else:
            self.journal["locations"].append({
                "address": address,
                "city": city,
                "state": state,
                "country": country,
                "years": years or [],
                "memories": memories or [],
                "added_at": datetime.now().isoformat()
            })

        self.save_journal()

    def add_education(self, institution: str, role: str, years: List[int] = None,
                      achievements: List[str] = None):
        """Add education entry"""
        self.journal["education"].append({
            "institution": institution,
            "role": role,
            "years": years or [],
            "achievements": achievements or [],
            "added_at": datetime.now().isoformat()
        })
        self.save_journal()

    def add_significant_event(self, event_type: str, description: str,
                              year: Optional[int] = None, context: Dict = None):
        """Add significant life event"""
        self.journal["significant_events"].append({
            "type": event_type,
            "description": description,
            "year": year,
            "context": context or {},
            "added_at": datetime.now().isoformat()
        })
        self.save_journal()

    def _extract_year_from_text(self, text: str) -> Optional[int]:
        """Try to extract a 4-digit year from text"""
        m = re.search(r'\b(19|20)\d{2}\b', text)
        if m:
            try:
                return int(m.group(0))
            except Exception:
                return None
        return None

    def extract_from_conversation(self, conversation_text: str, year_hints: List[int] = None):
        """
        Extract biographical information from conversation text
        Uses spaCy NER when available to identify PERSON, GPE/LOC, DATE and simple heuristics
        """
        text = conversation_text or ""
        text_lower = text.lower()

        # Quick simple heuristics (existing behavior) for some patterns
        if "friend" in text_lower or "met" in text_lower:
            # If spaCy is not available we can't reliably extract names; keep placeholder
            pass

        if "lived" in text_lower or "moved" in text_lower:
            # Placeholder without NLP
            pass

        # If spaCy is available, use NER to extract structured pieces
        if SPACY_AVAILABLE and nlp:
            try:
                doc = nlp(text)
                persons = set()
                geos = set()
                dates = set()
                orgs = set()

                for ent in doc.ents:
                    label = ent.label_.upper()
                    ent_text = ent.text.strip()
                    if label == "PERSON":
                        persons.add(ent_text)
                    elif label in ("GPE", "LOC", "FAC"):
                        geos.add(ent_text)
                    elif label in ("DATE", "TIME"):
                        dates.add(ent_text)
                    elif label == "ORG":
                        orgs.add(ent_text)

                # Add friends for PERSON entities
                for p in persons:
                    # Attempt to see if the context contains how they were met (simple heuristic)
                    met_at = None
                    relationship = None
                    # Example heuristic: "I met John at work" -> met_at = 'work'
                    m = re.search(r'\bmet\s+' + re.escape(p.split()[-1]) + r'\s+at\s+([A-Za-z0-9_ ]+)', text, flags=re.IGNORECASE)
                    if m:
                        met_at = m.group(1).strip()
                    self.add_friend(name=p, met_at=met_at, relationship=relationship, memories=[text[:200]])

                # Add locations for GPE/LOC entities
                for g in geos:
                    # We don't always have an address — store city/state as city if possible
                    city = g
                    address = g
                    # Try to extract a 4-digit year from surrounding text for timeframe
                    year = self._extract_year_from_text(text)
                    self.add_location(address=address, city=city, state=None, country="USA", years=[year] if year else None, memories=[text[:200]])

                # Add timeline entries for DATE entities or extracted year
                for d in dates:
                    year = self._extract_year_from_text(d)
                    if not year and year_hints:
                        # prefer year hint if provided
                        year = year_hints[0]
                    # Save a timeline entry describing the date mention
                    self.add_timeline_entry(year=year, content=f"Referenced date: {d}", context={"source": "ner", "snippet": text[:200]})

                # Add organizations as career/education hints
                # Only add as employer if there are clear employment indicators in the text
                employment_keywords = [
                    r'\bwork\s+(?:for|at|with)\b',
                    r'\bemployed\s+(?:by|at)\b',
                    r'\bjob\s+(?:at|with)\b',
                    r'\bworking\s+(?:for|at|with)\b',
                    r'\bcareer\s+(?:at|with)\b',
                    r'\bemployee\s+(?:of|at)\b',
                    r'\bhire\s+(?:by|at)\b',
                    r'\bposition\s+(?:at|with)\b'
                ]
                has_employment_context = any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in employment_keywords)
                
                for o in orgs:
                    # Simple heuristic: if 'university' or 'college' in name treat as education
                    if re.search(r'(university|college|school)', o, flags=re.IGNORECASE):
                        self.add_education(institution=o, role="attendee", years=None)
                    elif has_employment_context:
                        # Only add as employer if there are clear employment indicators
                        # Check if this organization is mentioned in employment context
                        org_in_employment_context = re.search(
                            r'(?:' + '|'.join([p.replace(r'\b', '') for p in employment_keywords]) + r')\s+' + re.escape(o),
                            text,
                            flags=re.IGNORECASE
                        )
                        if org_in_employment_context:
                            self.journal.setdefault("career", []).append({
                                "employer": o,
                                "notes": text[:200],
                                "added_at": datetime.now().isoformat()
                            })
                            self.save_journal()
                    # Otherwise, don't add organizations as employers - they're just mentioned in conversation

            except Exception:
                # If spaCy processing fails for any reason, fall back to minimal heuristics
                pass
        else:
            # If spaCy is not available, use some light-weight regex heuristics as a fallback

            # Try to pull names using a naive capitalized-word heuristic (very noisy)
            possible_names = re.findall(r'\b([A-Z][a-z]{1,}(?:\s+[A-Z][a-z]{1,})?)\b', text)
            # Filter out words that are likely to be sentence-starts or other false positives
            filtered = [n for n in possible_names if len(n) > 2 and not n.lower().startswith("i")]
            for name in filtered[:3]:
                self.add_friend(name=name, memories=[text[:200]])

            # Try to detect simple year mentions
            year = self._extract_year_from_text(text)
            if year:
                self.add_timeline_entry(year=year, content=f"Referenced year: {year}", context={"source": "regex", "snippet": text[:200]})

    def get_summary(self) -> str:
        """Get formatted summary of journal for LLM context"""
        summary_parts = []

        summary_parts.append(f"SUBJECT: {self.journal['subject']['name']}")
        summary_parts.append(f"Age: {self.journal['subject']['age']}")
        summary_parts.append(f"Location: {self.journal['subject']['location']}")
        summary_parts.append(f"Employer: {self.journal['subject']['employer']}")

        if self.journal["timeline"]:
            summary_parts.append(f"\nTIMELINE ENTRIES: {len(self.journal['timeline'])}")
            for entry in self.journal["timeline"][-10:]:  # Last 10 entries
                year_str = f"[{entry['year']}]" if entry.get("year") else "[Unknown Year]"
                summary_parts.append(f"  {year_str}: {entry['content'][:200]}")
        else:
            summary_parts.append("\nTIMELINE ENTRIES: None (journal is empty or just created)")

        if self.journal["friends"]:
            summary_parts.append(f"\nFRIENDS: {len(self.journal['friends'])}")
            for friend in self.journal["friends"][:10]:  # First 10
                friend_info = f"  - {friend['name']}"
                if friend.get('memories'):
                    friend_info += f" (memories: {', '.join(friend['memories'][:2])})"
                summary_parts.append(friend_info)
        else:
            summary_parts.append("\nFRIENDS: None recorded")

        if self.journal["locations"]:
            summary_parts.append(f"\nLOCATIONS: {len(self.journal['locations'])}")
            for loc in self.journal["locations"][:10]:
                summary_parts.append(f"  - {loc['city']}, {loc.get('state', loc.get('country', ''))}")
        else:
            summary_parts.append("\nLOCATIONS: None recorded")
        
        # Add other sections if they have data
        if self.journal.get("career"):
            summary_parts.append(f"\nCAREER: {len(self.journal['career'])} entries")
            for career_item in self.journal["career"][:5]:
                if isinstance(career_item, dict):
                    employer = career_item.get('employer', 'Unknown')
                    summary_parts.append(f"  - {employer}")
        
        if self.journal.get("relationships"):
            summary_parts.append(f"\nRELATIONSHIPS: {len(self.journal['relationships'])} entries")
            for rel in self.journal["relationships"][:5]:
                if isinstance(rel, dict):
                    rel_name = rel.get('name', rel.get('person', 'Unknown'))
                    summary_parts.append(f"  - {rel_name}")

        return "\n".join(summary_parts)

    def search(self, query: str) -> List[Dict]:
        """Search journal entries"""
        results = []
        query_lower = query.lower()
        
        # If query is about history/past in general, return all timeline entries
        history_keywords = ["history", "past", "remember", "before", "ago", "used to", 
                          "from my", "my history", "tell me something", "something about",
                          "tell me about"]
        is_general_history_query = any(keyword in query_lower for keyword in history_keywords)
        
        if is_general_history_query:
            # Return all timeline entries (most relevant for history queries)
            for entry in self.journal["timeline"]:
                results.append({"type": "timeline", "data": entry})
            # Also include friends and locations
            for friend in self.journal["friends"]:
                results.append({"type": "friend", "data": friend})
            for loc in self.journal["locations"]:
                results.append({"type": "location", "data": loc})
            return results

        # Otherwise, do keyword-based search
        # For CJS persona, expand search to include family-related keywords
        # If query mentions family terms, also search for Jim-related keywords
        family_keywords = ["parents", "parent", "mom", "mother", "dad", "father", "family"]
        jim_keywords = ["jim", "jim's prop shop", "carroll", "carroll james spohn", "dad", "father"]
        
        # If query contains family keywords, also search for Jim-related entries
        search_terms = [query_lower]
        if any(keyword in query_lower for keyword in family_keywords):
            search_terms.extend(jim_keywords)
        
        # Search timeline
        for entry in self.journal["timeline"]:
            content_lower = entry["content"].lower()
            # Check if any search term matches
            if any(term in content_lower for term in search_terms):
                results.append({"type": "timeline", "data": entry})

        # Search friends
        for friend in self.journal["friends"]:
            if query_lower in friend["name"].lower() or query_lower in str(friend.get("memories", [])).lower():
                results.append({"type": "friend", "data": friend})

        # Search locations
        for loc in self.journal["locations"]:
            if query_lower in loc["city"].lower() or query_lower in loc.get("address", "").lower():
                results.append({"type": "location", "data": loc})

        return results