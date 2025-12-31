"""
Task Service
Manages tasks and to-do items locally
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3


class TaskService:
    """Manages tasks and to-do items"""
    
    def __init__(self, db_path: str = "mo11y_companion.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize tasks database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date DATETIME,
                priority TEXT DEFAULT 'medium',
                importance INTEGER DEFAULT 5,
                status TEXT DEFAULT 'pending',
                completed BOOLEAN DEFAULT 0,
                completed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add importance column if it doesn't exist (migration for existing databases)
        try:
            cursor.execute("ALTER TABLE tasks ADD COLUMN importance INTEGER DEFAULT 5")
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
        
        conn.commit()
        conn.close()
    
    def add_task(self, title: str, description: Optional[str] = None,
                 due_date: Optional[datetime] = None,
                 priority: str = "medium", importance: int = 5) -> int:
        """Add a new task
        
        Args:
            title: Task title
            description: Task description
            due_date: Due date/time
            priority: Priority level ('high', 'medium', 'low')
            importance: Importance score (1-10, default 5)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tasks
            (title, description, due_date, priority, importance, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (title, description, due_date.isoformat() if due_date else None, priority, importance))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return task_id
    
    def get_tasks(self, status: Optional[str] = None,
                  priority: Optional[str] = None,
                  include_completed: bool = False) -> List[Dict]:
        """Get tasks with optional filters"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        
        if not include_completed:
            query += " AND completed = 0"
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        
        query += " ORDER BY importance DESC, priority DESC, due_date ASC, created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_pending_tasks(self) -> List[Dict]:
        """Get all pending tasks"""
        return self.get_tasks(status="pending", include_completed=False)
    
    def get_overdue_tasks(self) -> List[Dict]:
        """Get tasks that are overdue"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            SELECT * FROM tasks
            WHERE completed = 0
            AND due_date IS NOT NULL
            AND due_date < ?
            ORDER BY due_date ASC
        """, (now,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_task(self, task_id: int, title: Optional[str] = None,
                   description: Optional[str] = None,
                   due_date: Optional[datetime] = None,
                   priority: Optional[str] = None,
                   importance: Optional[int] = None,
                   status: Optional[str] = None):
        """Update a task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if due_date is not None:
            updates.append("due_date = ?")
            params.append(due_date.isoformat() if due_date else None)
        
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
        
        if importance is not None:
            updates.append("importance = ?")
            params.append(importance)
        
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(task_id)
            
            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
    
    def mark_completed(self, task_id: int):
        """Mark a task as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE tasks
            SET completed = 1,
                status = 'completed',
                completed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (task_id,))
        
        conn.commit()
        conn.close()
    
    def delete_task(self, task_id: int):
        """Delete a task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        
        conn.commit()
        conn.close()
    
    def get_task_summary(self) -> Dict:
        """Get summary statistics about tasks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total tasks
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed = 0")
        total_pending = cursor.fetchone()[0]
        
        # Overdue tasks
        now = datetime.now().isoformat()
        cursor.execute("""
            SELECT COUNT(*) FROM tasks
            WHERE completed = 0
            AND due_date IS NOT NULL
            AND due_date < ?
        """, (now,))
        overdue = cursor.fetchone()[0]
        
        # By priority
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed = 0 AND priority = 'high'")
        high_priority = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed = 0 AND priority = 'medium'")
        medium_priority = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed = 0 AND priority = 'low'")
        low_priority = cursor.fetchone()[0]
        
        # Completed tasks
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE completed = 1")
        completed = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_pending": total_pending,
            "overdue": overdue,
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "low_priority": low_priority,
            "completed": completed
        }
