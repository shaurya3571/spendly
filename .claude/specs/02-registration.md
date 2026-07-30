# Spec: Registration

## Overview
Implement user registration so new visitors can create a Spendly account. This step upgrades the existing stub `GET /register` route into a fully functional form that accepts a POST, validates input, hashes the password, and inserts a new row into the`users` table. On success the user is shown with a success message and then redirected to the login page. This is the entry point for all authenticated features that follow.

## Depends on
- Step 1 (Database setup) — requires `get_db()`, `init_db()`, and the `users` table to already exist in `database/db.py`.

## Routes
- `POST /register` - create a new user account from submitted form data - public
- `GET /register` - already implemented, unchanged - public

If validation fails or the email is already taken, `POST /register` re-renders `register.html` with an `error` message and a 400 status instead of redirecting.

## Database changes
No database changes. The `users` table (id, name, email, password_hash, created_at) already exists per `database/db.py` from Step 1. This step only adds query functions that use the existing schema — no new tables, columns, or constraints.

## Templates
- Create: none
- **Modify**:`templates/register.html` — Change the form`action`
to `url_for('register')` with method="post"`
- Add `name`attributes to all inputs:
`name`,`email`,`password`,`confirm_password`
- Add a block to display a flash error message (e.g."Email already registered","Passwords do not match")
- Keep all existing visual design

## Files to change
- `app.py` — upgrade `register()` to handle `GET` and `POST`; on `POST`, add flash + redirect logic
- `database/db.py` — add `create_user()`helper 
- `templates/register.html` — wire up form action/method and flash message display

## Files to create
None.

## New dependencies
No new dependencies. Uses `werkzeug.security.generate_password_hash` (already installed) and Flask's built in `flash` / `redirect` / `url_for`.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders) — never f-strings in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash` — never store plaintext
- `app.secret_key` must be set in `app.py` for `flash()` to work (use a hardcoded dev string for now)
- Server-side validation must check:
1. All fields are non-empty
2. `password == confirm_password`
3. Email is not already registered (catch `sqlite3.IntegrityError`)
- On any validation failure, re-render the form with a flashed error message - do not redirect
- On success, `flash` a success message and `redirect` to `url_for('login')`
- Use `abort(405)` if an unsupported HTTP method reaches the route
All templates extend `base.html`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `url_for()` for every internal link - never hardcode URLs

## Definition of done
- [ ] Submitting the register form with valid name, email, and password (≥8 chars) creates a new row in `users` with a hashed (not plaintext) password
- [ ] After successful registration, the browser is redirected to `GET /login`
- [ ] Submitting with an email that already exists in the database re-renders `register.html` with an error message and does not create a duplicate row
- [ ] Submitting with a name, missing/invalid email, or a password under 8 characters re-renders `register.html` with an appropriate error and does not insert a row
- [ ] The register form's `action` uses `{{ url_for('register') }}`, not a hardcoded path
- [ ] `GET /register` still renders registeration form normally with no error shown
- [ ] Password is stored as a hash - never plaintext - verifiable by inspecting `spendly.db`
- [ ] All new queries in `database/db.py` use `?` parameterized placeholders
- [ ] No duplicate user is created on repeated valid submissions with the same email
- [ ] App starts on port 5001 without errors and existing routes (`/`, `/login`, `/terms`, `/privacy`) are unaffected