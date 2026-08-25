"""Read-only query helpers for the profile page.

Deliberately separate from database/db.py (connection/schema/auth) — an
intentional, confirmed deviation from the project's usual single-file DB
convention, scoped to this feature.
"""

from datetime import datetime

from database.db import get_db


def _apply_date_range(sql, params, date_from, date_to):
    """Append a date-range filter to sql/params if both bounds are set."""
    if date_from is not None and date_to is not None:
        sql += " AND date BETWEEN ? AND ?"
        params.extend([date_from, date_to])
    return sql, params


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


def get_summary_stats(user_id, date_from=None, date_to=None):
    """Return {'total_spent', 'transaction_count', 'top_category',
    'top_category_amount'}. Zeros/sentinel if the user has no expenses."""
    conn = get_db()
    try:
        totals_sql = (
            "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt "
            "FROM expenses WHERE user_id = ?"
        )
        totals_params = [user_id]
        totals_sql, totals_params = _apply_date_range(totals_sql, totals_params, date_from, date_to)
        totals = conn.execute(totals_sql, totals_params).fetchone()

        top_sql = (
            "SELECT category, SUM(amount) AS cat_total FROM expenses "
            "WHERE user_id = ?"
        )
        top_params = [user_id]
        top_sql, top_params = _apply_date_range(top_sql, top_params, date_from, date_to)
        top_sql += " GROUP BY category ORDER BY cat_total DESC, category ASC LIMIT 1"
        top = conn.execute(top_sql, top_params).fetchone()
    finally:
        conn.close()
    return {
        "total_spent": round(totals["total"], 2),
        "transaction_count": totals["cnt"],
        "top_category": top["category"] if top else "—",
        "top_category_amount": round(top["cat_total"], 2) if top else 0,
    }


def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    """Return newest-first list of {'date','description','category','amount'}."""
    conn = get_db()
    try:
        sql = "SELECT date, description, category, amount FROM expenses WHERE user_id = ?"
        params = [user_id]
        sql, params = _apply_date_range(sql, params, date_from, date_to)
        sql += " ORDER BY date DESC, id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def get_category_breakdown(user_id, date_from=None, date_to=None):
    """Return list of {'name','amount','percent'} sorted by amount desc.
    percent values are ints summing to 100; the largest category absorbs
    the rounding remainder."""
    conn = get_db()
    try:
        sql = "SELECT category, SUM(amount) AS amount FROM expenses WHERE user_id = ?"
        params = [user_id]
        sql, params = _apply_date_range(sql, params, date_from, date_to)
        sql += " GROUP BY category ORDER BY amount DESC, category ASC"
        rows = conn.execute(sql, params).fetchall()
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
