"""Date-filter tests for the /profile route (Step 6).

Spec: .claude/specs/06-date-filter-profile.md

Seed-data assumptions (see tests/test_backend_connection.py and
database/db.py:seed_db): the demo user (demo_user_id == 1) has 8 seed
expenses, one per day for the 8 days immediately preceding
``date.today()`` at server-start time, totalling ₹277.50 across 7
categories, with "Shopping" as the top category (₹80.00, the single
largest expense). All test date ranges below are computed relative to
``date.today()`` / ``timedelta`` so they stay correct regardless of when
the suite runs.
"""

from datetime import date, timedelta

from database.queries import (
    get_category_breakdown,
    get_recent_transactions,
    get_summary_stats,
)

TODAY = date.today()

# Narrows to the 4 expenses seeded on days-2..days-5 ago:
#   day-2 Transport ₹12.00, day-3 Bills ₹60.00,
#   day-4 Health ₹45.00,   day-5 Entertainment ₹15.00
# Total = ₹132.00, top category = Bills (₹60.00, single largest in range)
NARROW_FROM = (TODAY - timedelta(days=5)).isoformat()
NARROW_TO = (TODAY - timedelta(days=2)).isoformat()

# A future range that cannot match any seed expense (all seed dates are
# in the past relative to TODAY).
EMPTY_FROM = (TODAY + timedelta(days=1)).isoformat()
EMPTY_TO = (TODAY + timedelta(days=5)).isoformat()

# date_from strictly after date_to -> invalid range.
INVALID_FROM = TODAY.isoformat()
INVALID_TO = (TODAY - timedelta(days=10)).isoformat()


# ============================================================
# Section 1: backward compatibility — explicit None == no date args
# ============================================================

def test_get_summary_stats_explicit_none_matches_no_args(demo_user_id):
    no_args = get_summary_stats(demo_user_id)
    explicit_none = get_summary_stats(demo_user_id, date_from=None, date_to=None)
    assert explicit_none == no_args, "date_from=None, date_to=None must match unfiltered call"


def test_get_recent_transactions_explicit_none_matches_no_args(demo_user_id):
    no_args = get_recent_transactions(demo_user_id)
    explicit_none = get_recent_transactions(demo_user_id, date_from=None, date_to=None)
    assert explicit_none == no_args, "date_from=None, date_to=None must match unfiltered call"


def test_get_category_breakdown_explicit_none_matches_no_args(demo_user_id):
    no_args = get_category_breakdown(demo_user_id)
    explicit_none = get_category_breakdown(demo_user_id, date_from=None, date_to=None)
    assert explicit_none == no_args, "date_from=None, date_to=None must match unfiltered call"


# ============================================================
# Section 2: happy path — /profile with no query params == Step 5 view
# ============================================================

def test_profile_no_query_params_matches_unfiltered_step5_view(authenticated_client):
    resp = authenticated_client.get("/profile")
    assert resp.status_code == 200
    assert b"277.50" in resp.data, "unfiltered total spent must be unchanged from Step 5"
    assert b"Shopping" in resp.data, "unfiltered top category must be unchanged from Step 5"
    assert "₹".encode() in resp.data, "currency symbol must be present"


# ============================================================
# Section 3: custom range narrows results — DB layer
# ============================================================

def test_get_summary_stats_custom_range_narrows_totals(demo_user_id):
    result = get_summary_stats(demo_user_id, date_from=NARROW_FROM, date_to=NARROW_TO)
    assert result["total_spent"] == 132.00
    assert result["transaction_count"] == 4
    assert result["top_category"] == "Bills"


def test_get_recent_transactions_custom_range_returns_only_in_range(demo_user_id):
    result = get_recent_transactions(demo_user_id, date_from=NARROW_FROM, date_to=NARROW_TO)
    assert len(result) == 4
    for item in result:
        assert NARROW_FROM <= item["date"] <= NARROW_TO
    assert result[0]["date"] >= result[-1]["date"], "must stay newest-first"
    descriptions = {item["description"] for item in result}
    assert descriptions == {"Bus pass", "Electricity", "Pharmacy", "Movie ticket"}


def test_get_category_breakdown_custom_range_returns_only_in_range_categories(demo_user_id):
    result = get_category_breakdown(demo_user_id, date_from=NARROW_FROM, date_to=NARROW_TO)
    assert len(result) == 4
    assert result[0]["name"] == "Bills"
    assert result[0]["amount"] == 60.00
    assert sum(c["percent"] for c in result) == 100
    names = {c["name"] for c in result}
    assert names == {"Transport", "Bills", "Health", "Entertainment"}


# ============================================================
# Section 4: custom range narrows results — route layer
# ============================================================

def test_profile_route_custom_range_narrows_all_sections(authenticated_client):
    resp = authenticated_client.get(
        f"/profile?date_from={NARROW_FROM}&date_to={NARROW_TO}"
    )
    assert resp.status_code == 200
    assert b"132.00" in resp.data, "total spent must reflect narrowed range"
    assert b"Bills" in resp.data, "top category must reflect narrowed range"
    assert b"Electricity" in resp.data, "in-range transaction must be listed"
    assert b"Groceries" not in resp.data, "out-of-range transaction must be excluded"
    assert b"New shoes" not in resp.data, "out-of-range transaction must be excluded"
    assert b"Miscellaneous" not in resp.data, "out-of-range transaction must be excluded"
    assert b"Restaurant" not in resp.data, "out-of-range transaction must be excluded"
    assert "₹".encode() in resp.data


# ============================================================
# Section 5: empty range — DB layer
# ============================================================

def test_get_summary_stats_empty_range_returns_zero_state(demo_user_id):
    result = get_summary_stats(demo_user_id, date_from=EMPTY_FROM, date_to=EMPTY_TO)
    assert result["total_spent"] == 0
    assert result["transaction_count"] == 0
    assert result["top_category"] == "—"


def test_get_recent_transactions_empty_range_returns_empty_list(demo_user_id):
    result = get_recent_transactions(demo_user_id, date_from=EMPTY_FROM, date_to=EMPTY_TO)
    assert result == []


def test_get_category_breakdown_empty_range_returns_empty_list(demo_user_id):
    result = get_category_breakdown(demo_user_id, date_from=EMPTY_FROM, date_to=EMPTY_TO)
    assert result == []


# ============================================================
# Section 6: empty range — route layer (no errors, ₹0.00 zero state)
# ============================================================

def test_profile_route_empty_range_returns_200_with_zero_state(authenticated_client):
    resp = authenticated_client.get(
        f"/profile?date_from={EMPTY_FROM}&date_to={EMPTY_TO}"
    )
    assert resp.status_code == 200, "a valid but empty range must not error"
    assert "₹0.00".encode() in resp.data, "total spent must show ₹0.00"
    assert b"No transactions yet." in resp.data, "transaction list must render its empty state"
    assert b"No expenses yet" in resp.data, "category breakdown must render its empty state"


# ============================================================
# Section 7: validation error — date_from after date_to
# ============================================================

def test_profile_route_invalid_range_falls_back_and_flashes_error(authenticated_client):
    resp = authenticated_client.get(
        f"/profile?date_from={INVALID_FROM}&date_to={INVALID_TO}"
    )
    assert resp.status_code == 200
    assert b"Start date must be before end date." in resp.data, (
        "an inverted range must produce the spec's flash error message"
    )
    assert b"277.50" in resp.data, "must fall back to the unfiltered total"
    assert b"Shopping" in resp.data, "must fall back to the unfiltered top category"


# ============================================================
# Section 8: malformed input does not crash — silent fallback
# ============================================================

def test_profile_route_malformed_date_from_does_not_crash(authenticated_client):
    resp = authenticated_client.get(
        f"/profile?date_from=not-a-date&date_to={TODAY.isoformat()}"
    )
    assert resp.status_code == 200, "malformed date_from must not produce a 500"
    assert b"277.50" in resp.data, "malformed input must silently fall back to unfiltered"


def test_profile_route_malformed_date_to_does_not_crash(authenticated_client):
    resp = authenticated_client.get(
        f"/profile?date_from={TODAY.isoformat()}&date_to=not-a-date"
    )
    assert resp.status_code == 200, "malformed date_to must not produce a 500"
    assert b"277.50" in resp.data, "malformed input must silently fall back to unfiltered"


def test_profile_route_sql_injection_attempt_in_date_from_does_not_crash(authenticated_client):
    resp = authenticated_client.get(
        "/profile?date_from='; DROP TABLE expenses; --&date_to=" + TODAY.isoformat()
    )
    assert resp.status_code == 200, "unparseable/malicious date_from must not produce a 500"
    assert b"277.50" in resp.data, "unfiltered fallback must still be shown"

    # The table must survive: a follow-up request still sees the seed data.
    follow_up = authenticated_client.get("/profile")
    assert follow_up.status_code == 200
    assert b"277.50" in follow_up.data, "expenses table must not have been affected"


# ============================================================
# Section 9: auth guard — with and without filter query params
# ============================================================

def test_profile_redirects_when_not_authenticated_no_filter_params(client):
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_profile_redirects_when_not_authenticated_with_filter_params(client):
    resp = client.get(f"/profile?date_from={NARROW_FROM}&date_to={NARROW_TO}")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


# ============================================================
# Section 10: currency formatting is present in every filter state
# ============================================================

def test_profile_route_shows_currency_symbol_unfiltered(authenticated_client):
    resp = authenticated_client.get("/profile")
    assert "₹".encode() in resp.data


def test_profile_route_shows_currency_symbol_custom_range(authenticated_client):
    resp = authenticated_client.get(
        f"/profile?date_from={NARROW_FROM}&date_to={NARROW_TO}"
    )
    assert "₹".encode() in resp.data


def test_profile_route_shows_currency_symbol_empty_range(authenticated_client):
    resp = authenticated_client.get(
        f"/profile?date_from={EMPTY_FROM}&date_to={EMPTY_TO}"
    )
    assert "₹".encode() in resp.data
