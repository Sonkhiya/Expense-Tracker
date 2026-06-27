"""Pytest fixtures for Spendly tests."""

import pytest
import tempfile
import os
import sqlite3
from datetime import date, timedelta

from app import app as flask_app
from database.db import get_db, init_db, DATABASE


@pytest.fixture
def app():
    """Create a Flask app instance with test config."""
    # Use a temporary database for testing
    db_fd, db_path = tempfile.mkstemp()
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "WTF_CSRF_ENABLED": False,
    })

    # Override the database path for this test
    import database.db
    original_db = DATABASE
    database.db.DATABASE = db_path

    with flask_app.app_context():
        init_db()
        yield flask_app

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)
    database.db.DATABASE = original_db


@pytest.fixture
def client(app):
    """Test client for the app."""
    return app.test_client()


@pytest.fixture
def db(app):
    """Database connection for direct queries."""
    with app.app_context():
        conn = get_db()
        yield conn
        conn.close()


@pytest.fixture
def seeded_db(app, db):
    """Database with seed data (demo user + expenses)."""
    from werkzeug.security import generate_password_hash

    with app.app_context():
        cursor = db.cursor()

        # Create demo user
        password_hash = generate_password_hash("demo123")
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", password_hash)
        )
        user_id = cursor.lastrowid

        # Insert sample expenses across different dates
        sample_expenses = [
            (user_id, 45.50, "Food", "2026-04-01", "Lunch at cafe"),
            (user_id, 25.00, "Transport", "2026-04-02", "Uber ride"),
            (user_id, 120.00, "Bills", "2026-04-03", "Electric bill"),
            (user_id, 35.00, "Health", "2026-04-05", "Pharmacy"),
            (user_id, 50.00, "Entertainment", "2026-04-07", "Movie tickets"),
            (user_id, 89.99, "Shopping", "2026-04-10", "New shirt"),
            (user_id, 15.00, "Other", "2026-04-12", "Miscellaneous"),
            (user_id, 65.00, "Food", "2026-04-15", "Dinner with friends"),
            # Add some May expenses for "last month" tests
            (user_id, 100.00, "Food", "2026-05-10", "Groceries"),
            (user_id, 75.00, "Transport", "2026-05-20", "Train ticket"),
            # Add some June expenses for "this month" tests
            (user_id, 200.00, "Bills", "2026-06-01", "Rent"),
            (user_id, 50.00, "Food", "2026-06-15", "Restaurant"),
        ]

        cursor.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            sample_expenses
        )
        db.commit()
        yield db


@pytest.fixture
def auth_client(client, seeded_db):
    """Authenticated test client logged in as demo user."""
    # Log in the user - CSRF is skipped in testing mode
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    }, follow_redirects=True)
    return client


@pytest.fixture
def csrf_token(client):
    """Get CSRF token from a form."""
    response = client.get("/login")
    # In tests we disable CSRF, but this fixture exists for completeness
    return "test-token"