# Spec: Registration

## Overview
This feature implements user registration for the Spendly expense tracker. Users can create an account by providing their name, email, password, and password confirmation. The registration form validates input, checks for duplicate emails, hashes passwords securely, and creates a new user record in the database. After successful registration, users are redirected to the login page to log in manually (no auto-login).

## Depends on
- Step 01: Database Setup (users table must exist with id, name, email, password_hash, created_at)

## Routes
- `GET /register` — Display registration form — public (already exists)
- `POST /register` — Handle registration form submission — public

## Database changes
No database changes. The users table from Step 01 already has all required columns.

## Templates
- **Create:** None
- **Modify:** `templates/register.html` — add form with name, email, password, password confirmation fields, CSRF token via session, validation error display, and link to login page

## Files to change
- `app.py` — add POST /register route with form handling, CSRF validation via session
- `templates/register.html` — implement registration form UI

## Files to create
None

## New dependencies
No new dependencies. Uses Flask's built-in `flash`, `url_for`, and `session`; werkzeug's `generate_password_hash` (already in project).

## Rules for implementation
- No SQLAlchemy or ORMs — use raw SQLite with parameterised queries only
- Passwords must be hashed with `werkzeug.security.generate_password_hash`
- Use Flask's `flash()` with categories: `flash("message", "success")` or `flash("message", "error")`
- Use `redirect(url_for())` for post-submit redirects
- CSRF protection: generate token via `session['csrf_token']`, validate on POST
- Validate: all fields required, email format valid, email unique, password minimum 6 characters, password and confirmation must match
- User is NOT auto-logged in after registration — redirect to `/login` only
- Use CSS variables from `style.css` — never hardcode hex values
- All templates must extend `base.html`

## Definition of done
- [ ] Registration form displays at `/register` with name, email, password, confirm password fields
- [ ] Form includes CSRF token (stored in session)
- [ ] Submitting empty fields shows validation error
- [ ] Invalid email format shows error
- [ ] Duplicate email shows error
- [ ] Password shorter than 6 characters shows error
- [ ] Password and confirmation mismatch shows error
- [ ] Successful registration creates user in database with hashed password
- [ ] After success, user is redirected to `/login` with flash success message
- [ ] Registration page has link to login page for existing users
