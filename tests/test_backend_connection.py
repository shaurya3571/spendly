"""Backend connection tests for the /profile route (Step 5)."""

from database.queries import (
    get_category_breakdown,
    get_recent_transactions,
    get_summary_stats,
)
from database.db import create_user


# ============================================================
# Subagent 1: transaction history
# ============================================================

def test_get_recent_transactions_returns_seed_data(demo_user_id):
    result = get_recent_transactions(demo_user_id)
    assert len(result) == 8
    assert result[0]["date"] >= result[-1]["date"]
    for item in result:
        assert set(["date", "description", "category", "amount"]).issubset(item.keys())


def test_get_recent_transactions_empty_for_new_user():
    new_user_id = create_user("Test User", "newuser-txn-test@example.com", "password123")
    result = get_recent_transactions(new_user_id)
    assert result == []


def test_profile_authenticated_shows_transactions(authenticated_client):
    resp = authenticated_client.get("/profile")
    assert resp.status_code == 200
    assert b"Groceries" in resp.data or b"Electricity" in resp.data


# ============================================================
# Subagent 2: summary stats
# ============================================================

def test_get_summary_stats_seed_user(demo_user_id):
    result = get_summary_stats(demo_user_id)
    assert result["total_spent"] == 277.50
    assert result["transaction_count"] == 8
    assert result["top_category"] == "Shopping"


def test_get_summary_stats_no_expenses():
    new_user_id = create_user("Test User", "newuser-stats-test@example.com", "password123")
    result = get_summary_stats(new_user_id)
    assert result["total_spent"] == 0
    assert result["transaction_count"] == 0
    assert result["top_category"] == "—"


def test_profile_authenticated_shows_stats(authenticated_client):
    resp = authenticated_client.get("/profile")
    assert resp.status_code == 200
    assert b"277.50" in resp.data
    assert b"Shopping" in resp.data


# ============================================================
# Subagent 3: category breakdown
# ============================================================

def test_get_category_breakdown_seed_user(demo_user_id):
    result = get_category_breakdown(demo_user_id)
    assert len(result) == 7
    assert result[0]["name"] == "Shopping"
    assert sum(c["percent"] for c in result) == 100


def test_get_category_breakdown_no_expenses():
    new_user_id = create_user("Test User", "newuser-cat-test@example.com", "password123")
    result = get_category_breakdown(new_user_id)
    assert result == []


def test_profile_authenticated_shows_categories(authenticated_client):
    resp = authenticated_client.get("/profile")
    assert resp.status_code == 200
    assert b"Shopping" in resp.data


# ============================================================
# Shared route tests (orchestrator-owned, not delegated)
# ============================================================

def test_profile_redirects_when_not_authenticated(client):
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_profile_authenticated_shows_member_info(authenticated_client):
    resp = authenticated_client.get("/profile")
    assert resp.status_code == 200
    assert b"Demo User" in resp.data
    assert b"demo@spendly.com" in resp.data
