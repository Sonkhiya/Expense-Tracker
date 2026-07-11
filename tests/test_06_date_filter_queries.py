"""Unit tests for date filter query helpers in database/queries.py."""

import pytest
from datetime import date

from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
    _build_date_filter
)
from database.db import get_db, init_db, DATABASE


@pytest.fixture
def test_db():
    """Create a temporary database for testing."""
    import tempfile
    import database.db

    db_fd, db_path = tempfile.mkstemp()
    original_db = DATABASE
    database.db.DATABASE = db_path

    conn = get_db()
    yield conn

    conn.close()
    os.close(db_fd)
    os.unlink(db_path)
    database.db.DATABASE = original_db


import os


@pytest.fixture
def seeded_test_db(test_db):
    """Database with test user and expenses."""
    from werkzeug.security import generate_password_hash

    cursor = test_db.cursor()

    # Create test user
    password_hash = generate_password_hash("demo123")
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Test User", "test@spendly.com", password_hash)
    )
    user_id = cursor.lastrowid

    # Insert test expenses across different dates
    test_expenses = [
        (user_id, 100.00, "Food", "2026-01-15", "Lunch"),
        (user_id, 200.00, "Transport", "2026-02-20", "Taxi"),
        (user_id, 300.00, "Food", "2026-03-10", "Dinner"),
        (user_id, 400.00, "Bills", "2026-04-05", "Electric"),
        (user_id, 500.00, "Food", "2026-05-12", "Groceries"),
        (user_id, 600.00, "Entertainment", "2026-06-18", "Movies"),
    ]
    cursor.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        test_expenses
    )
    test_db.commit()

    return test_db, user_id


class TestBuildDateFilter:
    """Tests for _build_date_filter helper function."""

    def test_both_none_returns_empty(self):
        """Both dates None returns empty where clause and params."""
        where, params = _build_date_filter(None, None)
        assert where == ""
        assert params == []

    def test_start_date_only(self):
        """start_date only adds date >= condition."""
        where, params = _build_date_filter(date(2026, 1, 1), None)
        assert where == "date >= ?"
        assert params == ["2026-01-01"]

    def test_end_date_only(self):
        """end_date only adds date <= condition."""
        where, params = _build_date_filter(None, date(2026, 12, 31))
        assert where == "date <= ?"
        assert params == ["2026-12-31"]

    def test_both_dates(self):
        """Both dates add both conditions."""
        where, params = _build_date_filter(date(2026, 1, 1), date(2026, 12, 31))
        assert where == "date >= ? AND date <= ?"
        assert params == ["2026-01-01", "2026-12-31"]


class TestGetSummaryStats:
    """Tests for get_summary_stats function."""

    def test_no_dates_returns_all_expenses(self, seeded_test_db):
        """No date params returns stats for all expenses."""
        db, user_id = seeded_test_db
        stats = get_summary_stats(user_id)
        assert stats["transaction_count"] == 6
        # Total = 100+200+300+400+500+600 = 2100
        assert stats["total_spent"] == "₹2,100.00"
        # Top category: Food has 100+300+500 = 900
        assert stats["top_category"] == "Food"

    def test_with_date_range_filters_correctly(self, seeded_test_db):
        """Date range filters stats correctly."""
        db, user_id = seeded_test_db
        # Jan to March only
        stats = get_summary_stats(user_id, date(2026, 1, 1), date(2026, 3, 31))
        assert stats["transaction_count"] == 3
        assert stats["total_spent"] == "₹600.00"  # 100+200+300
        assert stats["top_category"] == "Food"  # Food has 400, Transport has 200

    def test_start_date_only_filters_from_date(self, seeded_test_db):
        """start_date only filters from that date forward."""
        db, user_id = seeded_test_db
        stats = get_summary_stats(user_id, date(2026, 3, 1), None)
        # Should include March, April, May, June (300+400+500+600 = 1800)
        assert stats["transaction_count"] == 4
        assert stats["total_spent"] == "₹1,800.00"

    def test_end_date_only_filters_to_date(self, seeded_test_db):
        """end_date only filters up to that date."""
        db, user_id = seeded_test_db
        stats = get_summary_stats(user_id, None, date(2026, 3, 31))
        # Should include Jan, Feb, March (100+200+300 = 600)
        assert stats["transaction_count"] == 3
        assert stats["total_spent"] == "₹600.00"

    def test_user_with_no_expenses(self, test_db):
        """User with no expenses returns zeros."""
        from werkzeug.security import generate_password_hash
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Empty User", "empty@test.com", generate_password_hash("pass"))
        )
        user_id = cursor.lastrowid
        test_db.commit()

        stats = get_summary_stats(user_id)
        assert stats["total_spent"] == "₹0.00"
        assert stats["transaction_count"] == 0
        assert stats["top_category"] == "—"

    def test_invalid_user_id_returns_zeros(self, seeded_test_db):
        """Non-existent user returns zeros."""
        db, user_id = seeded_test_db
        stats = get_summary_stats(99999)
        assert stats["total_spent"] == "₹0.00"
        assert stats["transaction_count"] == 0
        assert stats["top_category"] == "—"


class TestGetRecentTransactions:
    """Tests for get_recent_transactions function."""

    def test_no_dates_returns_all_newest_first(self, seeded_test_db):
        """No dates returns all transactions newest first."""
        db, user_id = seeded_test_db
        txns = get_recent_transactions(user_id, limit=10)
        assert len(txns) == 6
        # Newest first: June, May, April, March, Feb, Jan
        assert txns[0]["date"] == "2026-06-18"
        assert txns[1]["date"] == "2026-05-12"
        assert txns[-1]["date"] == "2026-01-15"

    def test_date_range_filters_transactions(self, seeded_test_db):
        """Date range filters transactions correctly."""
        db, user_id = seeded_test_db
        txns = get_recent_transactions(user_id, date(2026, 1, 1), date(2026, 3, 31))
        assert len(txns) == 3
        for t in txns:
            assert "2026-01" <= t["date"] <= "2026-03"

    def test_start_date_only(self, seeded_test_db):
        """start_date only filters from date."""
        db, user_id = seeded_test_db
        txns = get_recent_transactions(user_id, date(2026-04-01), None)
        assert len(txns) == 3
        for t in txns:
            assert t["date"] >= "2026-04-01"

    def test_end_date_only(self, seeded_test_db):
        """end_date only filters to date."""
        db, user_id = seeded_test_db
        txns = get_recent_transactions(user_id, None, date(2026-03-31))
        assert len(txns) == 3
        for t in txns:
            assert t["date"] <= "2026-03-31"

    def test_limit_respected(self, seeded_test_db):
        """Limit parameter is respected."""
        db, user_id = seeded_test_db
        txns = get_recent_transactions(user_id, limit=2)
        assert len(txns) == 2

    def test_amounts_have_rupee_symbol(self, seeded_test_db):
        """Transaction amounts formatted with ₹."""
        db, user_id = seeded_test_db
        txns = get_recent_transactions(user_id)
        for t in txns:
            assert t["amount"].startswith("₹")

    def test_empty_result_for_no_matching_dates(self, seeded_test_db):
        """No matching dates returns empty list."""
        db, user_id = seeded_test_db
        txns = get_recent_transactions(user_id, date(2027, 1, 1), date(2027, 12, 31))
        assert txns == []


class TestGetCategoryBreakdown:
    """Tests for get_category_breakdown function."""

    def test_no_dates_returns_all_categories(self, seeded_test_db):
        """No dates returns breakdown for all expenses."""
        db, user_id = seeded_test_db
        cats = get_category_breakdown(user_id)
        # Categories: Food (900), Entertainment (600), Bills (400), Transport (200)
        assert len(cats) == 4
        # Sum of percentages = 100
        pct_sum = sum(c["pct"] for c in cats)
        assert pct_sum == 100

    def test_date_range_filters_categories(self, seeded_test_db):
        """Date range filters categories correctly."""
        db, user_id = seeded_test_db
        # Jan-March: Food (400), Transport (200)
        cats = get_category_breakdown(user_id, date(2026, 1, 1), date(2026, 3, 31))
        assert len(cats) == 2
        cat_names = [c["name"] for c in cats]
        assert "Food" in cat_names
        assert "Transport" in cat_names
        assert "Bills" not in cat_names
        assert "Entertainment" not in cat_names

    def test_percentages_sum_to_100(self, seeded_test_db):
        """Percentages always sum to 100."""
        db, user_id = seeded_test_db
        for params in [
            (None, None),
            (date(2026, 1, 1), date(2026, 3, 31)),
            (date(2026, 4, 1), date(2026, 6, 30)),
        ]:
            cats = get_category_breakdown(user_id, *params)
            if cats:
                pct_sum = sum(c["pct"] for c in cats)
                assert pct_sum == 100, f"Percentages sum to {pct_sum}: {cats}"

    def test_start_date_only(self, seeded_test_db):
        """start_date only works for categories."""
        db, user_id = seeded_test_db
        cats = get_category_breakdown(user_id, date(2026, 4, 1), None)
        cat_names = [c["name"] for c in cats]
        assert "Bills" in cat_names
        assert "Food" in cat_names
        assert "Entertainment" in cat_names
        assert "Transport" not in cat_names

    def test_end_date_only(self, seeded_test_db):
        """end_date only works for categories."""
        db, user_id = seeded_test_db
        cats = get_category_breakdown(user_id, None, date(2026, 3, 31))
        cat_names = [c["name"] for c in cats]
        assert "Food" in cat_names
        assert "Transport" in cat_names
        assert "Bills" not in cat_names

    def test_amounts_have_rupee_symbol(self, seeded_test_db):
        """Category amounts formatted with ₹."""
        db, user_id = seeded_test_db
        cats = get_category_breakdown(user_id)
        for c in cats:
            assert c["amount"].startswith("₹")

    def test_empty_result_returns_empty_list(self, seeded_test_db):
        """No matching expenses returns empty list."""
        db, user_id = seeded_test_db
        cats = get_category_breakdown(user_id, date(2027, 1, 1), date(2027, 12, 31))
        assert cats == []

    def test_category_structure_has_required_fields(self, seeded_test_db):
        """Each category has name, amount, percentage, pct."""
        db, user_id = seeded_test_db
        cats = get_category_breakdown(user_id)
        for c in cats:
            assert "name" in c
            assert "amount" in c
            assert "percentage" in c
            assert "pct" in c
            assert isinstance(c["pct"], int)
            # percentage should match pct value
            assert c["percentage"] == c["pct"]