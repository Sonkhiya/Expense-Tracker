# Spec: Login and Logout

## Overview
This feature implements user authentication for the Spendly expense tracker. Users can sign in with their email and password, which creates a session. The login form validates credentials against the database, establishes a session on success, and shows appropriate error messages on failure. Logout clears the session and redirects to the landing page. This is the first step in implementing authentication, building on the registration feature from Step 02.

## Depends on
- Step 01: Database Setup (users table must exist)
- Step 02: Registration (users can create accounts)

## Routes
- `GET /login` — Display login form — public (already exists)
- `POST /login` — Handle login form submission — public
- `GET /logout` — Clear session and redirect to landing — logged-in users

## Database changes
No database changes. Uses existing users table from Step 01.

## Templates
- **Create:** None
- **Modify:** `templates/login.html` — add form action for POST, CSRF token, validation error display, flash message display

## Files to change
- `app.py` — implement POST /login route with credential validation and session creation, implement GET /logout with session clear
- `templates/login.html` — add CSRF token field, error display section for flash messages

## Files to create
None

## New dependencies
No new dependencies. Uses Flask's built-in `session`, `flash`, `url_for`; werkzeug's `check_password_hash` (already in project).

## Rules for implementation
- No SQLAlchemy or ORMs — use raw SQLite with parameterised queries only
- Passwords must be verified with `werkzeug.security.check_password_hash`
- Use Flask's `flash()` with categories: `flash("message", "success")` or `flash("message", "error")`
- Use `redirect(url_for())` for post-submit redirects
- CSRF protection: generate token via `session['csrf_token']`, validate on POST
- Validate: email and password required, credentials must match database record
- On successful login: store user_id in session, redirect to landing page
- On failed login: show error, redirect back to login form
- Logout must clear all session data and redirect to landing page with success message
- Use CSS variables from `style.css` — never hardcode hex values
- All templates must extend `base.html`

## Definition of done
- [ ] Login form at `/login` accepts email and password via POST
- [ ] Form includes CSRF token (stored in session)
- [ ] Submitting empty fields shows validation error
- [ ] Invalid email format shows error
- [ ] Non-existent email shows error (without revealing whether email exists)
- [ ] Wrong password shows error
- [ ] Successful login stores user_id in session
- [ ] Successful login redirects to landing page with flash success message
- [ ] Logout clears session data
- [ ] Logout redirects to landing page with flash success message
