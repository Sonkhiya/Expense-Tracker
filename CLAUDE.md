# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Spendly - A Flask-based expense tracking web application. This is an educational project where students implement features incrementally following step-by-step instructions.

## Commands

```bash
# Run the application
python app.py

# Run tests
pytest

# Run specific test
pytest -k test_name
```

## Architecture

- **app.py** - Main Flask application with routes for landing, auth (login/register/logout), and placeholder routes for expenses CRUD
- **database/db.py** - Database layer (students implement `get_db()`, `init_db()`, `seed_db()` for SQLite with row_factory and foreign keys)
- **templates/** - Jinja2 HTML templates (base.html provides navbar/footer layout)
- **static/** - CSS (style.css) and JavaScript (main.js)

## Development Notes

- Routes use function-based views; auth and expense features are built incrementally
- Database uses SQLite; `database/db.py` is empty except for comments outlining the required functions
- The app runs on port 5001 in debug mode
