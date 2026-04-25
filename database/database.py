"""
Smart Student Expense Tracker - Database Module
Group 9 | Database Developer: Light Ahana (ENG-219-058/2024)

Database: SQLite
Tables:
    - users         : stores student accounts
    - categories    : spending categories (food, transport, etc.)
    - expenses      : individual expense records
    - budgets       : monthly budget limits per category
    - savings_goals : savings targets set by the student
"""

import sqlite3
import os
from datetime import datetime

# ──────────────────────────────────────────────
# DATABASE CONFIGURATION
# ──────────────────────────────────────────────

DB_NAME = "expense_tracker.db"


def get_connection():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row        # allows dict-style access: row["column"]
    conn.execute("PRAGMA foreign_keys = ON")  # enforce FK constraints
    return conn


# ──────────────────────────────────────────────
# SCHEMA CREATION
# ──────────────────────────────────────────────

def create_tables():
    """Create all tables if they do not already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. USERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name   TEXT    NOT NULL,
            username    TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            email       TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # 2. CATEGORIES TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL UNIQUE,
            description   TEXT
        )
    """)

    # 3. EXPENSES TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            expense_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            category_id   INTEGER NOT NULL,
            amount        REAL    NOT NULL CHECK(amount > 0),
            description   TEXT,
            date          TEXT    DEFAULT (date('now')),
            created_at    TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id)     REFERENCES users(user_id)      ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE RESTRICT
        )
    """)

    # 4. BUDGETS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            budget_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            category_id   INTEGER NOT NULL,
            monthly_limit REAL    NOT NULL CHECK(monthly_limit > 0),
            month         TEXT    NOT NULL,   -- format: YYYY-MM
            FOREIGN KEY (user_id)     REFERENCES users(user_id)      ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE,
            UNIQUE(user_id, category_id, month)
        )
    """)

    # 5. SAVINGS GOALS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS savings_goals (
            goal_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            goal_name     TEXT    NOT NULL,
            target_amount REAL    NOT NULL CHECK(target_amount > 0),
            saved_amount  REAL    DEFAULT 0.0,
            deadline      TEXT,
            status        TEXT    DEFAULT 'active',  -- active / completed / cancelled
            created_at    TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Tables created successfully.")


def seed_default_categories():
    """Insert default expense categories (runs only if table is empty)."""
    defaults = [
        ("Food & Drinks",   "Meals, snacks, beverages"),
        ("Transport",       "Bus, matatu, fuel"),
        ("Accommodation",   "Rent, hostel fees"),
        ("Education",       "Books, stationery, printing"),
        ("Entertainment",   "Movies, events, outings"),
        ("Healthcare",      "Medicine, clinic visits"),
        ("Clothing",        "Clothes, shoes, accessories"),
        ("Airtime & Data",  "Mobile recharge and internet bundles"),
        ("Personal Care",   "Hygiene, grooming"),
        ("Miscellaneous",   "Other expenses"),
    ]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO categories (name, description) VALUES (?, ?)", defaults
        )
        conn.commit()
        print("[DB] Default categories seeded.")
    conn.close()


# ──────────────────────────────────────────────
# USER OPERATIONS
# ──────────────────────────────────────────────

def register_user(full_name, username, password, email=None):
    """
    Register a new student account.
    Returns the new user_id, or None if username already exists.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (full_name, username, password, email) VALUES (?, ?, ?, ?)",
            (full_name, username, password, email)
        )
        conn.commit()
        user_id = cursor.lastrowid
        print(f"[DB] User '{username}' registered with ID {user_id}.")
        return user_id
    except sqlite3.IntegrityError:
        print(f"[DB] Username '{username}' already exists.")
        return None
    finally:
        conn.close()


def login_user(username, password):
    """
    Validate login credentials.
    Returns the user row (as dict) if valid, else None.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password)
    )
    user = cursor.fetchone()
    conn.close()
    if user:
        print(f"[DB] User '{username}' logged in successfully.")
        return dict(user)
    print("[DB] Invalid username or password.")
    return None


def get_user_by_id(user_id):
    """Fetch a user record by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


# ──────────────────────────────────────────────
# CATEGORY OPERATIONS
# ──────────────────────────────────────────────

def get_all_categories():
    """Return all available spending categories."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_category(name, description=""):
    """Add a custom category. Returns new category_id or None on duplicate."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            (name, description)
        )
        conn.commit()
        cid = cursor.lastrowid
        print(f"[DB] Category '{name}' added with ID {cid}.")
        return cid
    except sqlite3.IntegrityError:
        print(f"[DB] Category '{name}' already exists.")
        return None
    finally:
        conn.close()


# ──────────────────────────────────────────────
# EXPENSE OPERATIONS
# ──────────────────────────────────────────────

def add_expense(user_id, category_id, amount, description="", date=None):
    """
    Record a new expense entry.
    date format: 'YYYY-MM-DD'. Defaults to today if not provided.
    Returns the new expense_id.
    """
    if date is None:
        date = datetime.today().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO expenses (user_id, category_id, amount, description, date)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, category_id, amount, description, date)
    )
    conn.commit()
    eid = cursor.lastrowid
    conn.close()
    print(f"[DB] Expense added: ID {eid}, Amount {amount}, Date {date}.")
    return eid


def get_expenses_by_user(user_id, start_date=None, end_date=None, category_id=None):
    """
    Retrieve all expenses for a user, with optional date range and category filters.
    Returns a list of dicts with expense + category name joined.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT e.expense_id, e.amount, e.description, e.date,
               c.name AS category_name
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = ?
    """
    params = [user_id]

    if start_date:
        query += " AND e.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND e.date <= ?"
        params.append(end_date)
    if category_id:
        query += " AND e.category_id = ?"
        params.append(category_id)

    query += " ORDER BY e.date DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_expense(expense_id, amount=None, description=None, date=None, category_id=None):
    """Update one or more fields of an existing expense."""
    conn = get_connection()
    cursor = conn.cursor()
    fields, params = [], []

    if amount is not None:
        fields.append("amount = ?"); params.append(amount)
    if description is not None:
        fields.append("description = ?"); params.append(description)
    if date is not None:
        fields.append("date = ?"); params.append(date)
    if category_id is not None:
        fields.append("category_id = ?"); params.append(category_id)

    if not fields:
        print("[DB] No fields to update.")
        conn.close()
        return False

    params.append(expense_id)
    cursor.execute(f"UPDATE expenses SET {', '.join(fields)} WHERE expense_id = ?", params)
    conn.commit()
    conn.close()
    print(f"[DB] Expense {expense_id} updated.")
    return True


def delete_expense(expense_id):
    """Delete an expense record by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE expense_id = ?", (expense_id,))
    conn.commit()
    conn.close()
    print(f"[DB] Expense {expense_id} deleted.")


# ──────────────────────────────────────────────
# BUDGET OPERATIONS
# ──────────────────────────────────────────────

def set_budget(user_id, category_id, monthly_limit, month=None):
    """
    Set or update a monthly budget for a category.
    month format: 'YYYY-MM'. Defaults to current month.
    """
    if month is None:
        month = datetime.today().strftime("%Y-%m")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO budgets (user_id, category_id, monthly_limit, month)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(user_id, category_id, month)
           DO UPDATE SET monthly_limit = excluded.monthly_limit""",
        (user_id, category_id, monthly_limit, month)
    )
    conn.commit()
    conn.close()
    print(f"[DB] Budget set: {monthly_limit} for category {category_id} in {month}.")


def get_budget_vs_spending(user_id, month=None):
    """
    Return a summary of budget vs actual spending per category for a given month.
    Each row: { category_name, monthly_limit, total_spent, remaining }
    """
    if month is None:
        month = datetime.today().strftime("%Y-%m")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.name AS category_name,
               b.monthly_limit,
               COALESCE(SUM(e.amount), 0.0) AS total_spent,
               (b.monthly_limit - COALESCE(SUM(e.amount), 0.0)) AS remaining
        FROM budgets b
        JOIN categories c ON b.category_id = c.category_id
        LEFT JOIN expenses e
               ON e.user_id = b.user_id
              AND e.category_id = b.category_id
              AND strftime('%Y-%m', e.date) = ?
        WHERE b.user_id = ? AND b.month = ?
        GROUP BY b.budget_id
        ORDER BY c.name
    """, (month, user_id, month))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────
# SAVINGS GOAL OPERATIONS
# ──────────────────────────────────────────────

def add_savings_goal(user_id, goal_name, target_amount, deadline=None):
    """Create a new savings goal. Returns the new goal_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO savings_goals (user_id, goal_name, target_amount, deadline)
           VALUES (?, ?, ?, ?)""",
        (user_id, goal_name, target_amount, deadline)
    )
    conn.commit()
    gid = cursor.lastrowid
    conn.close()
    print(f"[DB] Savings goal '{goal_name}' created with ID {gid}.")
    return gid


def update_savings(goal_id, amount_to_add):
    """Add an amount to a savings goal's saved_amount."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE savings_goals SET saved_amount = saved_amount + ? WHERE goal_id = ?",
        (amount_to_add, goal_id)
    )
    # auto-complete if target reached
    cursor.execute("""
        UPDATE savings_goals
        SET status = 'completed'
        WHERE goal_id = ? AND saved_amount >= target_amount AND status = 'active'
    """, (goal_id,))
    conn.commit()
    conn.close()
    print(f"[DB] Added {amount_to_add} to goal {goal_id}.")


def get_savings_goals(user_id):
    """Return all savings goals for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM savings_goals WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────
# REPORT / SUMMARY QUERIES
# ──────────────────────────────────────────────

def get_monthly_summary(user_id, month=None):
    """
    Total spending per category for a given month.
    Returns list of { category_name, total_spent }.
    """
    if month is None:
        month = datetime.today().strftime("%Y-%m")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.name AS category_name,
               SUM(e.amount) AS total_spent
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = ?
          AND strftime('%Y-%m', e.date) = ?
        GROUP BY c.category_id
        ORDER BY total_spent DESC
    """, (user_id, month))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_total_spent(user_id, month=None):
    """Return the grand total spent by a user in a given month."""
    if month is None:
        month = datetime.today().strftime("%Y-%m")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0.0) AS grand_total
        FROM expenses
        WHERE user_id = ?
          AND strftime('%Y-%m', date) = ?
    """, (user_id, month))
    result = cursor.fetchone()
    conn.close()
    return result["grand_total"] if result else 0.0


def check_budget_alerts(user_id, month=None):
    """
    Return categories where spending has reached or exceeded the budget.
    Returns list of { category_name, monthly_limit, total_spent, percent_used }.
    """
    rows = get_budget_vs_spending(user_id, month)
    alerts = []
    for row in rows:
        if row["monthly_limit"] > 0:
            percent = (row["total_spent"] / row["monthly_limit"]) * 100
            if percent >= 80:      # alert at 80 % threshold
                row["percent_used"] = round(percent, 1)
                alerts.append(row)
    return alerts


# ──────────────────────────────────────────────
# INITIALISATION
# ──────────────────────────────────────────────

def init_db():
    """Full database initialisation: create tables + seed default categories."""
    create_tables()
    seed_default_categories()
    print("[DB] Database initialised and ready.")


# Run init when module is first imported or executed directly
if __name__ == "__main__":
    init_db()
