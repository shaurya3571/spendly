"""Read-only query helpers for the profile page.

Deliberately separate from database/db.py (connection/schema/auth) — an
intentional, confirmed deviation from the project's usual single-file DB
convention, scoped to this feature.
"""

from datetime import datetime

from database.db import get_db


def get_user_by_id(user_id):
    """Return {'name', 'email', 'member_since'} or None."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    created = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
    return {
        "name": row["name"],
        "email": row["email"],
        "member_since": created.strftime("%B %Y"),
    }


def get_summary_stats(user_id):
    """Return {'total_spent', 'transaction_count', 'top_category',
    'top_category_amount'}. Zeros/sentinel if the user has no expenses."""
    conn = get_db()
    try:
        totals = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt "
            "FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        top = conn.execute(
            "SELECT category, SUM(amount) AS cat_total FROM expenses "
            "WHERE user_id = ? GROUP BY category "
            "ORDER BY cat_total DESC, category ASC LIMIT 1",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()
    return {
        "total_spent": round(totals["total"], 2),
        "transaction_count": totals["cnt"],
        "top_category": top["category"] if top else "—",
        "top_category_amount": round(top["cat_total"], 2) if top else 0,
    }


def get_recent_transactions(user_id, limit=10):
    """Return newest-first list of {'date','description','category','amount'}."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT date, description, category, amount FROM expenses "
            "WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def get_category_breakdown(user_id):
    """Return list of {'name','amount','percent'} sorted by amount desc.
    percent values are ints summing to 100; the largest category absorbs
    the rounding remainder."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT category, SUM(amount) AS amount FROM expenses "
            "WHERE user_id = ? GROUP BY category "
            "ORDER BY amount DESC, category ASC",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        return []
    total = sum(r["amount"] for r in rows)
    percents = [round((r["amount"] / total) * 100) for r in rows]
    percents[0] += 100 - sum(percents)  # largest absorbs rounding remainder
    return [
        {"name": r["category"], "amount": round(r["amount"], 2), "percent": p}
        for r, p in zip(rows, percents)
    ]
