#!/usr/bin/env python3
"""
Add or update bills from command line or natural language
Usage examples:
  python3 add_bill.py "TVEC electric is disconnected on the 7th of January 2026 and is $297.78"
  python3 add_bill.py "Electric Bill" 297.78 "2026-01-07" --importance 9 --category utilities
"""

import json
import os
import re
import sys
from datetime import datetime
from financial_service import FinancialService

def parse_natural_language(text: str) -> dict:
    """Parse natural language bill description"""
    text_lower = text.lower()
    result = {}
    
    # Extract amount (look for $X.XX or X.XX dollars - prioritize decimal amounts)
    # Try to find amounts with decimals first (more specific)
    amount_match = re.search(r'\$(\d+\.\d{2})', text)
    if not amount_match:
        amount_match = re.search(r'\$(\d+)', text)
    if not amount_match:
        amount_match = re.search(r'(\d+\.\d{2})\s*(?:dollars?|USD)?', text_lower)
    if amount_match:
        result['amount'] = float(amount_match.group(1))
    
    # Extract date (look for dates like "January 7, 2026" or "2026-01-07" or "7th of January 2026")
    date_patterns = [
        (r'(\d+)(?:st|nd|rd|th)?\s+of\s+(\w+)\s+(\d{4})', 'day_month_year'),  # "7th of January 2026"
        (r'(\w+)\s+(\d+)(?:st|nd|rd|th)?,?\s+(\d{4})', 'month_day_year'),  # "January 7, 2026"
        (r'(\d{4})-(\d{2})-(\d{2})', 'iso'),  # "2026-01-07"
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', 'slash'),  # "1/7/2026"
    ]
    
    months = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2,
        'march': 3, 'mar': 3, 'april': 4, 'apr': 4,
        'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
        'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10, 'november': 11, 'nov': 11,
        'december': 12, 'dec': 12
    }
    
    for pattern_tuple in date_patterns:
        pattern, pattern_type = pattern_tuple
        match = re.search(pattern, text_lower)
        if match:
            groups = match.groups()
            try:
                if pattern_type == 'day_month_year':  # "7th of January 2026"
                    day, month_name, year = int(groups[0]), groups[1], int(groups[2])
                    month = months.get(month_name.lower(), None)
                    if month:
                        result['due_date'] = datetime(year, month, day)
                        break
                elif pattern_type == 'month_day_year':  # "January 7, 2026"
                    month_name, day, year = groups[0], int(groups[1]), int(groups[2])
                    month = months.get(month_name.lower(), None)
                    if month:
                        result['due_date'] = datetime(year, month, day)
                        break
                elif pattern_type == 'iso':  # "2026-01-07"
                    result['due_date'] = datetime(int(groups[0]), int(groups[1]), int(groups[2]))
                    break
                elif pattern_type == 'slash':  # "1/7/2026"
                    result['due_date'] = datetime(int(groups[2]), int(groups[0]), int(groups[1]))
                    break
            except (ValueError, IndexError, KeyError) as e:
                continue
    
    # Extract bill name (look for company/service names)
    # Common patterns: "X is disconnected", "X bill", "X payment"
    name_patterns = [
        r'([A-Z][A-Za-z\s]+?)\s+(?:is|bill|payment|due)',
        r'([A-Z][A-Za-z\s]+?)\s+\$',
        r'bill[:\s]+([A-Z][A-Za-z\s]+)',
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip()
            # Clean up common words
            name = re.sub(r'\s+(is|bill|payment|due|disconnected)$', '', name, flags=re.IGNORECASE)
            if len(name) > 2:
                result['name'] = name
                break
    
    # Extract importance keywords
    if any(word in text_lower for word in ['critical', 'important', 'urgent', 'essential']):
        result['importance'] = 9
    elif any(word in text_lower for word in ['high', 'major']):
        result['importance'] = 7
    elif any(word in text_lower for word in ['low', 'minor']):
        result['importance'] = 3
    else:
        result['importance'] = 5  # default
    
    # Extract category
    if 'electric' in text_lower or 'power' in text_lower:
        result['category'] = 'utilities'
    elif 'water' in text_lower or 'sewer' in text_lower:
        result['category'] = 'utilities'
    elif 'mortgage' in text_lower or 'rent' in text_lower:
        result['category'] = 'housing'
    elif 'phone' in text_lower or 'cell' in text_lower:
        result['category'] = 'utilities'
    elif 'internet' in text_lower or 'cable' in text_lower:
        result['category'] = 'utilities'
    elif 'credit' in text_lower or 'card' in text_lower:
        result['category'] = 'debt'
    
    return result

def main():
    # Get database path from config
    config_path = "config.json"
    db_path = "mo11y_companion.db"
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            db_path = config.get("db_path", "mo11y_companion.db")
    
    financial = FinancialService(db_path)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print('  python3 add_bill.py "TVEC electric is disconnected on the 7th of January 2026 and is $297.78"')
        print('  python3 add_bill.py "Electric Bill" 297.78 "2026-01-07" --importance 9 --category utilities')
        sys.exit(1)
    
    # If first argument looks like natural language (contains words, not just numbers)
    if len(sys.argv) == 2 and re.search(r'[a-zA-Z]', sys.argv[1]):
        # Parse natural language
        text = sys.argv[1]
        parsed = parse_natural_language(text)
        
        if 'name' not in parsed:
            parsed['name'] = input("Bill name: ").strip()
        if 'amount' not in parsed:
            amount_str = input("Amount: $").strip()
            parsed['amount'] = float(amount_str.replace('$', ''))
        if 'due_date' not in parsed:
            date_str = input("Due date (YYYY-MM-DD): ").strip()
            parsed['due_date'] = datetime.fromisoformat(date_str)
        
        print(f"\nParsed bill information:")
        print(f"  Name: {parsed.get('name', 'Unknown')}")
        print(f"  Amount: ${parsed.get('amount', 0):.2f}")
        print(f"  Due date: {parsed.get('due_date', 'Unknown')}")
        print(f"  Importance: {parsed.get('importance', 5)}/10")
        print(f"  Category: {parsed.get('category', 'None')}")
        
        confirm = input("\nAdd this bill? (y/n): ").strip().lower()
        if confirm == 'y':
            # Check if bill with same name exists
            existing_bills = financial.get_all_bills()
            matching_bills = [b for b in existing_bills if b.get('name', '').lower() == parsed['name'].lower()]
            
            if matching_bills:
                print(f"\nFound existing bill: {matching_bills[0]['name']}")
                update = input("Update existing bill? (y/n): ").strip().lower()
                if update == 'y':
                    bill_id = matching_bills[0]['id']
                    financial.update_bill(bill_id, **{k: v for k, v in parsed.items() if k != 'due_date'})
                    if 'due_date' in parsed:
                        financial.update_bill(bill_id, due_date=parsed['due_date'])
                    print(f"✅ Updated bill: {matching_bills[0]['name']}")
                else:
                    bill_id = financial.add_bill(
                        name=parsed['name'],
                        amount=parsed['amount'],
                        due_date=parsed['due_date'],
                        importance=parsed.get('importance', 5),
                        category=parsed.get('category')
                    )
                    print(f"✅ Added new bill: {parsed['name']}")
            else:
                bill_id = financial.add_bill(
                    name=parsed['name'],
                    amount=parsed['amount'],
                    due_date=parsed['due_date'],
                    importance=parsed.get('importance', 5),
                    category=parsed.get('category')
                )
                print(f"✅ Added bill: {parsed['name']}")
        else:
            print("Cancelled.")
    else:
        # Command-line arguments
        name = sys.argv[1]
        amount = float(sys.argv[2])
        due_date_str = sys.argv[3]
        due_date = datetime.fromisoformat(due_date_str)
        
        # Parse optional arguments
        importance = 5
        category = None
        
        i = 4
        while i < len(sys.argv):
            if sys.argv[i] == '--importance' and i + 1 < len(sys.argv):
                importance = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == '--category' and i + 1 < len(sys.argv):
                category = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        # Check if bill exists
        existing_bills = financial.get_all_bills()
        matching_bills = [b for b in existing_bills if b.get('name', '').lower() == name.lower()]
        
        if matching_bills:
            bill_id = matching_bills[0]['id']
            financial.update_bill(bill_id, name=name, amount=amount, due_date=due_date, 
                                 importance=importance, category=category)
            print(f"✅ Updated bill: {name}")
        else:
            bill_id = financial.add_bill(name, amount, due_date, importance=importance, category=category)
            print(f"✅ Added bill: {name}")

if __name__ == '__main__':
    main()
