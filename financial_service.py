"""
Financial Service
Manages bills, payments, and financial tracking
Tracks bills, due dates, amounts, importance, and payment trends
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3


class FinancialService:
    """Manages financial tracking: bills, payments, and trends"""
    
    def __init__(self, db_path: str = "mo11y_companion.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize financial database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Bills table - recurring and one-time bills
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                due_date DATETIME NOT NULL,
                frequency TEXT DEFAULT 'monthly',
                importance INTEGER DEFAULT 5,
                category TEXT,
                account_number TEXT,
                payee TEXT,
                auto_pay BOOLEAN DEFAULT 0,
                is_paid BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Payment history table - tracks when bills were actually paid
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id INTEGER NOT NULL,
                due_date DATETIME NOT NULL,
                paid_date DATETIME,
                amount REAL NOT NULL,
                amount_paid REAL,
                is_on_time BOOLEAN,
                days_late INTEGER,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bill_id) REFERENCES bills(id)
            )
        """)
        
        # Paydates table - tracks when you get paid
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paydates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paydate DATETIME NOT NULL,
                amount REAL,
                source TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add importance column if it doesn't exist (migration)
        try:
            cursor.execute("ALTER TABLE bills ADD COLUMN importance INTEGER DEFAULT 5")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE bills ADD COLUMN category TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE bills ADD COLUMN account_number TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE bills ADD COLUMN payee TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE bills ADD COLUMN auto_pay BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        
        conn.commit()
        conn.close()
    
    def add_bill(self, name: str, amount: float, due_date: datetime,
                 frequency: str = "monthly", importance: int = 5,
                 description: Optional[str] = None, category: Optional[str] = None,
                 account_number: Optional[str] = None, payee: Optional[str] = None,
                 auto_pay: bool = False) -> int:
        """Add a new bill
        
        Args:
            name: Bill name (e.g., "Electric Bill", "Mortgage")
            amount: Bill amount
            due_date: Due date
            frequency: 'monthly', 'quarterly', 'yearly', 'one-time'
            importance: Importance score (1-10, default 5)
            description: Optional description
            category: Category (e.g., "utilities", "housing", "insurance")
            account_number: Account number
            payee: Payee name
            auto_pay: Whether it's on auto-pay
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO bills
            (name, description, amount, due_date, frequency, importance, 
             category, account_number, payee, auto_pay, is_paid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (name, description, amount, due_date.isoformat(), frequency, 
              importance, category, account_number, payee, auto_pay))
        
        bill_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return bill_id
    
    def get_upcoming_bills(self, days_ahead: int = 30) -> List[Dict]:
        """Get bills due within the next N days"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        now = datetime.now()
        end_date = now + timedelta(days=days_ahead)
        
        cursor.execute("""
            SELECT * FROM bills
            WHERE is_paid = 0
            AND due_date >= ?
            AND due_date <= ?
            ORDER BY importance DESC, due_date ASC
        """, (now.isoformat(), end_date.isoformat()))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_overdue_bills(self) -> List[Dict]:
        """Get bills that are overdue"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            SELECT * FROM bills
            WHERE is_paid = 0
            AND due_date < ?
            ORDER BY importance DESC, due_date ASC
        """, (now,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_all_bills(self, include_paid: bool = False) -> List[Dict]:
        """Get all bills"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM bills"
        if not include_paid:
            query += " WHERE is_paid = 0"
        query += " ORDER BY importance DESC, due_date ASC"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def mark_bill_paid(self, bill_id: int, paid_date: Optional[datetime] = None,
                       amount_paid: Optional[float] = None, notes: Optional[str] = None):
        """Mark a bill as paid and record payment history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get bill details
        cursor.execute("SELECT due_date, amount FROM bills WHERE id = ?", (bill_id,))
        bill = cursor.fetchone()
        if not bill:
            conn.close()
            return
        
        due_date_str, amount = bill
        due_date = datetime.fromisoformat(due_date_str)
        paid_dt = paid_date or datetime.now()
        
        # Calculate if on time
        is_on_time = paid_dt <= due_date
        days_late = 0
        if not is_on_time:
            days_late = (paid_dt - due_date).days
        
        # Record payment history
        cursor.execute("""
            INSERT INTO payment_history
            (bill_id, due_date, paid_date, amount, amount_paid, is_on_time, days_late, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (bill_id, due_date.isoformat(), paid_dt.isoformat(), amount,
              amount_paid or amount, is_on_time, days_late, notes))
        
        # Mark bill as paid
        cursor.execute("""
            UPDATE bills
            SET is_paid = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (bill_id,))
        
        conn.commit()
        conn.close()
    
    def add_paydate(self, paydate: datetime, amount: Optional[float] = None,
                   source: Optional[str] = None, notes: Optional[str] = None) -> int:
        """Add a paydate (when you get paid)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO paydates (paydate, amount, source, notes)
            VALUES (?, ?, ?, ?)
        """, (paydate.isoformat(), amount, source, notes))
        
        paydate_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return paydate_id
    
    def get_paydates(self, start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None) -> List[Dict]:
        """Get paydates within a date range"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM paydates WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND paydate >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND paydate <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY paydate DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_payment_trends(self, months: int = 6) -> Dict:
        """Analyze payment trends: on-time vs late payments"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=months * 30)
        
        # Get payment statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_payments,
                SUM(CASE WHEN is_on_time = 1 THEN 1 ELSE 0 END) as on_time_count,
                SUM(CASE WHEN is_on_time = 0 THEN 1 ELSE 0 END) as late_count,
                AVG(days_late) as avg_days_late,
                MAX(days_late) as max_days_late
            FROM payment_history
            WHERE paid_date >= ?
        """, (start_date.isoformat(),))
        
        stats = cursor.fetchone()
        
        # Get bills vs paydates comparison
        cursor.execute("""
            SELECT paydate, amount FROM paydates
            WHERE paydate >= ?
            ORDER BY paydate
        """, (start_date.isoformat(),))
        
        paydates = cursor.fetchall()
        
        cursor.execute("""
            SELECT due_date, amount FROM bills
            WHERE due_date >= ?
            ORDER BY due_date
        """, (start_date.isoformat(),))
        
        bills = cursor.fetchall()
        
        conn.close()
        
        total_payments, on_time_count, late_count, avg_days_late, max_days_late = stats
        
        on_time_rate = (on_time_count / total_payments * 100) if total_payments > 0 else 0
        
        return {
            "period_months": months,
            "total_payments": total_payments or 0,
            "on_time_count": on_time_count or 0,
            "late_count": late_count or 0,
            "on_time_rate": round(on_time_rate, 2),
            "avg_days_late": round(avg_days_late or 0, 1),
            "max_days_late": max_days_late or 0,
            "paydates": [{"date": p[0], "amount": p[1]} for p in paydates],
            "bills_due": [{"date": b[0], "amount": b[1]} for b in bills]
        }
    
    def get_financial_summary(self) -> Dict:
        """Get financial summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Upcoming bills total
        upcoming = self.get_upcoming_bills(30)
        upcoming_total = sum(bill.get('amount', 0) for bill in upcoming)
        
        # Overdue bills total
        overdue = self.get_overdue_bills()
        overdue_total = sum(bill.get('amount', 0) for bill in overdue)
        
        # This month's bills
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        month_end = datetime(now.year, now.month + 1, 1) if now.month < 12 else datetime(now.year + 1, 1, 1)
        
        cursor.execute("""
            SELECT SUM(amount) FROM bills
            WHERE due_date >= ? AND due_date < ?
            AND is_paid = 0
        """, (month_start.isoformat(), month_end.isoformat()))
        
        month_total = cursor.fetchone()[0] or 0
        
        # High importance bills
        cursor.execute("""
            SELECT COUNT(*) FROM bills
            WHERE importance >= 8
            AND is_paid = 0
            AND due_date >= ?
        """, (now.isoformat(),))
        
        high_importance_count = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "upcoming_bills_count": len(upcoming),
            "upcoming_bills_total": round(upcoming_total, 2),
            "overdue_bills_count": len(overdue),
            "overdue_bills_total": round(overdue_total, 2),
            "month_total": round(month_total, 2),
            "high_importance_count": high_importance_count
        }
    
    def update_bill(self, bill_id: int, name: Optional[str] = None,
                   amount: Optional[float] = None,
                   due_date: Optional[datetime] = None,
                   importance: Optional[int] = None,
                   **kwargs):
        """Update a bill"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if amount is not None:
            updates.append("amount = ?")
            params.append(amount)
        
        if due_date is not None:
            updates.append("due_date = ?")
            params.append(due_date.isoformat())
        
        if importance is not None:
            updates.append("importance = ?")
            params.append(importance)
        
        for key, value in kwargs.items():
            if value is not None:
                updates.append(f"{key} = ?")
                params.append(value)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(bill_id)
            
            query = f"UPDATE bills SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
    
    def delete_bill(self, bill_id: int):
        """Delete a bill"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
        
        conn.commit()
        conn.close()
