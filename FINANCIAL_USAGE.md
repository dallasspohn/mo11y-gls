# Financial Service Usage Guide

## How to Add or Update Bills

### Method 1: Natural Language (Recommended)

You can add bills using natural language through the `add_bill.py` script:

```bash
python3 add_bill.py "TVEC electric is disconnected on the 7th of January 2026 and is $297.78"
```

The script will:
- Parse the bill name, amount, and due date from your text
- Detect importance level (if mentioned)
- Detect category (utilities, housing, etc.)
- Ask for confirmation before adding
- Update existing bills if a matching name is found

**Examples:**
```bash
# Add a bill
python3 add_bill.py "Mortgage payment is $1850 due January 1st 2026"

# Update existing bill
python3 add_bill.py "TVEC electric is disconnected on the 7th of January 2026 and is $297.78"
```

### Method 2: Command Line Arguments

For more control, use explicit arguments:

```bash
python3 add_bill.py "Bill Name" 297.78 "2026-01-07" --importance 9 --category utilities
```

**Arguments:**
- Bill name (required)
- Amount (required)
- Due date in YYYY-MM-DD format (required)
- `--importance` (optional, 1-10, default 5)
- `--category` (optional: utilities, housing, debt, entertainment, etc.)

### Method 3: Through Conversation with Alex

You can also tell Alex to add bills:

```
You: "Add a bill for TVEC electric, $297.78, due January 7th 2026"
Alex: [Will detect financial action and can use the financial service]
```

Alex will detect keywords like:
- "add bill", "new bill", "create bill"
- "update bill", "change bill"
- "bill", "payment", "due"

### Method 4: Direct Python Code

```python
from financial_service import FinancialService
from datetime import datetime

financial = FinancialService("SPOHNZ.db")  # or your db path

# Add a new bill
bill_id = financial.add_bill(
    name="TVEC Electric",
    amount=297.78,
    due_date=datetime(2026, 1, 7),
    frequency="monthly",
    importance=9,
    category="utilities",
    description="Disconnection date"
)

# Update existing bill
financial.update_bill(
    bill_id,
    name="TVEC Electric",
    amount=297.78,
    due_date=datetime(2026, 1, 7),
    importance=9
)

# Mark bill as paid
financial.mark_bill_paid(bill_id, paid_date=datetime.now())
```

## Updating Existing Bills

The system will automatically detect if a bill with the same name exists and ask if you want to update it. You can also:

1. **Update by name**: The `add_bill.py` script checks for matching names
2. **Update by ID**: Use `financial.update_bill(bill_id, ...)` in code
3. **Update through conversation**: Tell Alex "Update the TVEC electric bill to $297.78"

## Viewing Bills

Ask Alex:
- "What bills are due?"
- "Show me my upcoming bills"
- "What's overdue?"
- "Show me payment trends"
- "What's my financial summary?"

## Bill Properties

- **Name**: Bill name (e.g., "TVEC Electric")
- **Amount**: Dollar amount (e.g., 297.78)
- **Due Date**: When the bill is due
- **Frequency**: 'monthly', 'quarterly', 'yearly', 'one-time'
- **Importance**: 1-10 scale (10 = critical, 1 = low)
- **Category**: utilities, housing, debt, entertainment, insurance, etc.
- **Payee**: Who to pay (optional)
- **Account Number**: Account number (optional)
- **Auto-pay**: Whether it's on auto-pay (boolean)
- **Description**: Additional notes

## Payment Tracking

When you mark a bill as paid, the system tracks:
- Payment date vs due date
- Whether payment was on-time
- Days late (if applicable)
- Payment trends over time

Use `financial.mark_bill_paid(bill_id)` to record payments.
