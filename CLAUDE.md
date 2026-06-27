# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Spendly - A Flask-based expense tracking web application. Educational project where students implement features incrementally following step-by-step specs in `.claude/specs/`.

## Commands

```bash
# Run the application (port 5002, debug mode)
python app.py

# Run tests
pytest

# Run specific test
pytest -k test_name

# Seed expenses for a user
python seed_expense.py <user_id> <count> <months>

# Seed demo Indian user (creates user + 50 expenses over 6 months)
python seed_indian_user.py
```

## Architecture

- **app.py** - Main Flask application with routes for landing, auth (login/register/logout), profile, and placeholder routes for expenses CRUD
- **database/db.py** - Database layer with `get_db()`, `init_db()`, `seed_db()` for SQLite (row_factory + foreign keys)
- **database/queries.py** - Query helpers (to be created in Step 5) for profile data
- **templates/** - Jinja2 HTML templates (base.html provides navbar/footer layout)
- **static/** - CSS (style.css) and JavaScript (main.js)

## Development Notes

- Routes use function-based views; auth and expense features built incrementally per specs
- Database uses SQLite; `database/db.py` implements all required functions
- App runs on port **5002** in debug mode (note: CLAUDE.md previously said 5001)
- Indian Rupee (₹) used for all currency display
- CSRF protection via session tokens on forms
- All templates extend `base.html`

## Database Schema

```sql
users:
  id INTEGER PRIMARY KEY AUTOINCREMENT
  name TEXT NOT NULL
  email TEXT UNIQUE NOT NULL
  password_hash TEXT NOT NULL
  created_at TEXT DEFAULT (datetime('now'))

expenses:
  id INTEGER PRIMARY KEY AUTOINCREMENT
  user_id INTEGER NOT NULL REFERENCES users(id)
  amount REAL NOT NULL
  category TEXT NOT NULL
  date TEXT NOT NULL
  description TEXT
  created_at TEXT DEFAULT (datetime('now'))
```

## Current Status

The project has completed:
- Step 1: Database setup (`database/db.py`)
- Step 2: Registration (`/register` route)
- Step 3: Login/Logout (`/login`, `/logout` routes)
- Step 4: Profile page static UI (`templates/profile.html`)

**Currently working on:** Step 5 - Backend routes for profile page (connecting `/profile` to real database queries)

## Key Files to Know

| File | Purpose |
|------|---------|
| `app.py` | Main Flask app with all routes |
| `database/db.py` | Database connection, init, seed |
| `database/queries.py` | Query helpers for profile (to be created) |
| `templates/profile.html` | Profile page with 4 dynamic sections |
| `templates/base.html` | Base layout with navbar/footer |
| `.claude/specs/05-backend-routes-for-profile-page.md` | Current step specification |