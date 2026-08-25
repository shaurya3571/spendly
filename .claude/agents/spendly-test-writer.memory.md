# Spendly test-writer — institutional memory

Persistent notes for future test-writing sessions. Append, don't rewrite.

## Fixtures (tests/conftest.py) — as actually implemented (differs from the
generic template in this agent's own prompt)
- `app` fixture: patches `database.db.DB_PATH` to a tempfile *before*
  `app.py` is imported (module-level patch at top of the first test file
  that ran, `test_backend_connection.py`), then just sets `TESTING=True`.
  No per-test DB reset — the DB is a shared tempfile seeded once via
  `seed_db()` at `app` import time. Tests must be read-only or use
  `create_user(...)` to get a fresh, isolated user rather than mutating
  the demo user's rows.
- `client` fixture: NOT defined in conftest.py — comes from `pytest-flask`
  (in requirements.txt), which auto-provides `client` from the `app`
  fixture. Do not redefine it.
- `demo_user_id` fixture: hardcoded `1` — the seeded "Demo User" /
  demo@spendly.com account.
- `authenticated_client` fixture: logs in by writing directly to the
  session (`sess["user_id"] = demo_user_id`), not via POST /login.

## Seed data (database/db.py:seed_db(), used by demo_user_id == 1)
8 expenses, one per day for days-1..days-8 before `date.today()` at
server-start time (so tests must compute ranges relative to
`date.today()`/`timedelta`, never hardcode absolute dates):
- day-1 Food ₹25.50 "Groceries"
- day-2 Transport ₹12.00 "Bus pass"
- day-3 Bills ₹60.00 "Electricity"
- day-4 Health ₹45.00 "Pharmacy"
- day-5 Entertainment ₹15.00 "Movie ticket"
- day-6 Shopping ₹80.00 "New shoes"
- day-7 Other ₹10.00 "Miscellaneous"
- day-8 Food ₹30.00 "Restaurant"
Totals: ₹277.50, 8 transactions, 7 categories, top category "Shopping".

## Routes / auth
- `GET /profile` — protected, redirects unauthenticated to `/login` (302).
  Accepts optional `date_from`/`date_to` query params (Step 6, ISO
  `YYYY-MM-DD`), see below.
- `GET /register`, `GET/POST /login`, `GET /logout` — implemented.
- `GET /expenses/add`, `GET /expenses/<id>/edit`, `GET /expenses/<id>/delete`
  — still stubs as of Step 6 (return plain "coming in Step N" strings). Do
  not write tests for these until their own step is active.

## database/queries.py (profile page read helpers, separate from db.py)
- `get_user_by_id(user_id)`, `get_summary_stats(user_id, date_from=None,
  date_to=None)`, `get_recent_transactions(user_id, limit=10,
  date_from=None, date_to=None)`, `get_category_breakdown(user_id,
  date_from=None, date_to=None)`.
- All three date-aware helpers only apply the `BETWEEN` filter when BOTH
  `date_from` and `date_to` are non-None; a single param present is
  equivalent to unfiltered. This is spec-mandated backward-compat
  behavior, not just an implementation detail — safe to assert on.
- No-expense / empty-range sentinel values: `total_spent` 0,
  `transaction_count` 0, `top_category` "—" (em-dash), empty list `[]`
  for transactions and category breakdown.

## Step 6 date-filter specifics (see .claude/specs/06-date-filter-profile.md)
- Date validation happens ONLY in `app.py` (`_parse_date`, strptime
  `%Y-%m-%d`, ValueError -> None). The DB-layer query helpers never see
  malformed strings — don't write DB-layer tests for malformed input,
  only route-level tests.
- `date_from > date_to` (both valid) -> both reset to None, flash
  `"Start date must be before end date."` (category "error"), falls back
  to unfiltered. Exact message text is spec-mandated, safe to assert
  verbatim.
- Malformed/partial params (one missing or unparseable) -> silently
  fall back to unfiltered, NO flash message, no 500.
- Flash messages render directly into `resp.data` via `base.html`'s
  `get_flashed_messages` block (`<div class="flash flash-{category}">`)
  — plain `b"..." in resp.data` assertions work fine, no need to follow
  redirects or inspect session.
- `templates/profile.html` empty-state landmark text (byte-string safe,
  avoid the literal em-dash char in assertions):
  - transactions: `b"No transactions yet."`
  - category breakdown: `b"No expenses yet"` (full string has a
    non-ASCII em-dash after it — match the prefix only)
- Currency values render as `f"₹{amount:.2f}"` — assert `"₹".encode() in
  resp.data` or the specific formatted string e.g. `"₹0.00".encode()`.

## Test files covering this route so far
- `tests/test_backend_connection.py` — Step 5, unfiltered
  get_summary_stats/get_recent_transactions/get_category_breakdown, plus
  shared auth-guard and member-info route tests. Uses `create_user(...)`
  for "empty state" users.
- `tests/test_06-date-filter-profile.py` — Step 6, date-filter behavior:
  backward-compat (explicit None == no args), narrowed custom range
  (DB layer + route layer, using day-2..day-5 seed window = ₹132.00 / 4
  txns / top category "Bills"), empty future-date range (zero state, DB
  + route), invalid range flash+fallback, malformed/SQL-injection-string
  fallback (no 500, table survives), auth guard with/without filter
  params, currency symbol present in all three filter states.
  Note: filename intentionally has a hyphen after the numeric prefix
  (`test_06-date-filter-profile.py`) to mirror the spec filename
  (`06-date-filter-profile.md`) — pytest collects it fine since it's
  never `import`ed by name, only discovered.

## Gotchas discovered
- Don't derive expected numeric assertions (totals, top category, etc.)
  by reading `database/queries.py`'s SQL/rounding logic and copying it
  back — always compute expected values independently from the spec +
  known seed data, or the test becomes tautological with the
  implementation instead of a correctness contract.
- `_parse_date`/query-helper backward-compat behavior treats "one date
  param present, one absent/malformed" as fully unfiltered (not a
  half-open range) — don't assume SQLite-style open-ended BETWEEN
  behavior.
