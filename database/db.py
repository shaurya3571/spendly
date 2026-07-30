import sqlite3
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

DB_PATH = "spendly.db"

CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()


def create_user(name, email, password):
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def seed_db():
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing > 0:
        conn.close()
        return

    password_hash = generate_password_hash("demo123")
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash),
    )
    user_id = cursor.lastrowid

    today = date.today()
    sample_expenses = [
        (25.50, "Food", (today - timedelta(days=1)).isoformat(), "Groceries"),
        (12.00, "Transport", (today - timedelta(days=2)).isoformat(), "Bus pass"),
        (60.00, "Bills", (today - timedelta(days=3)).isoformat(), "Electricity"),
        (45.00, "Health", (today - timedelta(days=4)).isoformat(), "Pharmacy"),
        (15.00, "Entertainment", (today - timedelta(days=5)).isoformat(), "Movie ticket"),
        (80.00, "Shopping", (today - timedelta(days=6)).isoformat(), "New shoes"),
        (10.00, "Other", (today - timedelta(days=7)).isoformat(), "Miscellaneous"),
        (30.00, "Food", (today - timedelta(days=8)).isoformat(), "Restaurant"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [(user_id, amount, category, d, desc) for amount, category, d, desc in sample_expenses],
    )
    conn.commit()
    conn.close()
