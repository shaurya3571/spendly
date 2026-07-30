# Spec: Login And Logout

## Overview
Implement session-based authentication so registered users can sign in and out of Spendly. This step upgrades the existing stub `GET /login` route to also handle `POST`, verifying submitted credentials against the `users` table and starting a Flask session on success. It also replaces the `GET /logout` placeholder with a real implementation that clears the session. This is the second half of the authentication flow started in Step 2 (Registration) and is a prerequisite for any route that needs to know who the current user is (Profile in Step 4, Expenses in Steps 7-9).

## Depends on
- Step 1 (Database setup) — requires `get_db()` and the `users` table to already exist in `database/db.py`.
- Step 2 (Registration) — requires `create_user()` so accounts with hashed passwords exist to log in with.

## Routes
- `GET /login` - already implemented, unchanged - public
- `POST /login` - authenticate a user by email/password and start a session - public
- `GET /logout` - clear the current session and redirect to the landing page - public (safe to call whether or not a session is active)

If credentials are invalid, `POST /login` re-renders `login.html` with a flashed error and a 400 status instead of redirecting.

## Database changes
No database changes. The `users` table (id, name, email, password_hash, created_at) already exists per `database/db.py` from Step 1. This step only adds a read query helper that uses the existing schema — no new tables, columns, or constraints.

## Templates
- Create: none
- **Modify**: `templates/login.html` — change the form `action` from the hardcoded `"/login"` to `{{ url_for('login') }}`; remove the local `{% if error %}` / `auth-error` block and rely on `base.html`'s existing flash-stack for error display (matches the pattern already used by `register.html`)
- **Modify**: `templates/base.html` — nav links become conditional on session state: show "Sign in" / "Get started" when logged out (current behavior); show a single plain "Sign out" link (`{{ url_for('logout') }}`) when `session` contains a `user_id`. No username and no CTA button styling in the navbar.

## Files to change
- `app.py` — upgrade `login()` to handle `GET` and `POST`; on `POST`, verify credentials, set `session['user_id']`, flash + redirect; implement `logout()` to clear the session and redirect
- `database/db.py` — add `verify_user()` helper
- `templates/login.html` — wire up form action and remove local error block
- `templates/base.html` — conditional nav based on session state

## Files to create
None.

## New dependencies
No new dependencies. Uses `werkzeug.security.check_password_hash` (already installed alongside `generate_password_hash`) and Flask's built-in `session`, `flash`, `redirect`, `url_for`.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders) — never f-strings in SQL
- Passwords hashed with `werkzeug.security` — verify with `check_password_hash`, never compare plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `url_for()` for every internal link — never hardcode URLs
- Use Flask's `session` object for auth state; store `session['user_id']` and `session['user_name']` (the navbar reads the name directly) — no custom cookies or tokens
- On invalid login, show one generic error message (e.g. "Invalid email or password") regardless of whether the email exists or the password is wrong — do not reveal which field was incorrect
- Server-side validation on `POST /login` must check:
  1. Both `email` and `password` are non-empty
  2. `verify_user()` finds a user with that email and confirms the password via `check_password_hash()`
- On any validation failure, re-render `login.html` with a flashed error and a 400 status — do not redirect
- On success, `flash` a welcome message, set `session['user_id']`, and `redirect` to `url_for('landing')`
- `GET /logout` must clear the session (e.g. `session.clear()`), flash a confirmation message, and redirect to `url_for('landing')` — it must not error if no session exists
- `GET /login` and `GET /register` must redirect an already-logged-in user to `url_for('landing')` — an authenticated user has no reason to see either form
- Use `abort(405)` if an unsupported HTTP method reaches `/login`

## Definition of done
- [ ] Submitting the login form with the seeded demo account (`demo@spendly.com` / `demo123`) sets `session['user_id']` and redirects to `GET /`
- [ ] Submitting the login form with a correct email but wrong password re-renders `login.html` with a generic flashed error and does not set a session
- [ ] Submitting the login form with an email that doesn't exist re-renders `login.html` with the same generic flashed error (no hint that the email is unregistered)
- [ ] Submitting with a missing email or password re-renders `login.html` with an appropriate error and does not set a session
- [ ] The login form's `action` uses `{{ url_for('login') }}`, not a hardcoded path
- [ ] After logging in, the navbar shows a single "Sign out" link instead of "Sign in" / "Get started" — no username, no button styling
- [ ] Visiting `GET /login` or `GET /register` while logged in redirects to `GET /` instead of rendering the form
- [ ] Visiting `GET /logout` while logged in clears the session and redirects to `GET /`, and the navbar reverts to "Sign in" / "Get started"
- [ ] Visiting `GET /logout` while not logged in does not raise an error and redirects to `GET /`
- [ ] `GET /login` still renders the login form normally with no error shown
- [ ] All new queries in `database/db.py` use `?` parameterized placeholders
- [ ] App starts on port 5001 without errors and existing routes (`/`, `/register`, `/terms`, `/privacy`) are unaffected
