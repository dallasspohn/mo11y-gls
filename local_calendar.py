"""
Local Calendar Integration
Simple calendar functionality
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3


class LocalCalendar:
    """Simple local calendar implementation"""
    
    def __init__(self, db_path: str = "mo11y_companion.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize calendar database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_event(self, title: str, start_time: datetime,
                 end_time: Optional[datetime] = None,
                 description: Optional[str] = None):
        """Add a calendar event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO calendar_events
            (title, description, start_time, end_time)
            VALUES (?, ?, ?, ?)
        """, (title, description, start_time.isoformat(),
              end_time.isoformat() if end_time else None))
        
        conn.commit()
        conn.close()
    
    def get_events(self, start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> List[Dict]:
        """Get calendar events"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM calendar_events WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND start_time >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND start_time <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY start_time"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
