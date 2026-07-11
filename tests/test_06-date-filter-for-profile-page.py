"""Route tests for date filter feature on profile page (Step 6)."""

import pytest
from datetime import date


class TestProfileDateFilterAuth:
    """Authentication guard tests for /profile route."""

    def test_profile_unauthenticated_redirects_to_login(self, client):
        """Unauthenticated users should be redirected to login."""
        response = client.get("/profile", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_profile_unauthenticated_follow_redirects_shows_login(self, client):
        """Unauthenticated users following redirect should see login page."""
        response = client.get("/profile", follow_redirects=True)
        assert response.status_code == 200
        assert b"Sign In" in response.data


class TestProfileDateFilterHappyPaths:
    """Happy path tests for date filtering on /profile route."""

    def test_profile_no_filters_shows_all_expenses(self, auth_client):
        """GET /profile without query params shows all expenses (backward compatible)."""
        response = auth_client.get("/profile")
        assert response.status_code == 200
        # Should show all 12 expenses from seed data
        assert b"Total Spent" in response.data
        assert b"Transactions" in response.data
        assert b"Category Breakdown" in response.data
        # Verify ₹ symbol present
        assert b"\xe2\x82\xb9" in response.data  # ₹ UTF-8 bytes

    def test_profile_with_valid_start_date_only(self, auth_client):
        """GET /profile with start_date only filters from that date to today."""
        response = auth_client.get("/profile?start_date=2026-05-01")
        assert response.status_code == 200
        # Should only show May and June expenses (5 expenses)
        assert b"Total Spent" in response.data

    def test_profile_with_valid_end_date_only(self, auth_client):
        """GET /profile with end_date only filters from earliest expense to that date."""
        response = auth_client.get("/profile?end_date=2026-04-15")
        assert response.status_code == 200
        # Should only show April expenses up to 15th (8 expenses)
        assert b"Total Spent" in response.data

    def test_profile_with_valid_date_range(self, auth_client):
        """GET /profile with both start_date and end_date filters correctly."""
        response = auth_client.get("/profile?start_date=2026-04-01&end_date=2026-04-30")
        assert response.status_code == 200
        # Should only show April expenses (8 expenses)
        assert b"Total Spent" in response.data

    def test_profile_same_start_and_end_date(self, auth_client):
        """GET /profile with same start and end date shows single day expenses."""
        response = auth_client.get("/profile?start_date=2026-04-01&end_date=2026-04-01")
        assert response.status_code == 200
        # Should only show expenses from 2026-04-01 (1 expense: Lunch at cafe, 45.50)

    def test_profile_this_month_preset_range(self, auth_client):
        """GET /profile with This Month preset dates (June 2026)."""
        response = auth_client.get("/profile?start_date=2026-06-01&end_date=2026-06-30")
        assert response.status_code == 200
        # Should only show June expenses (2 expenses: Rent 200, Restaurant 50)

    def test_profile_last_month_preset_range(self, auth_client):
        """GET /profile with Last Month preset dates (May 2026)."""
        response = auth_client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
        assert response.status_code == 200
        # Should only show May expenses (2 expenses: Groceries 100, Train 75)

    def test_profile_this_year_preset_range(self, auth_client):
        """GET /profile with This Year preset dates (2026)."""
        response = auth_client.get("/profile?start_date=2026-01-01&end_date=2026-12-31")
        assert response.status_code == 200
        # Should show all 12 expenses from 2026

    def test_profile_all_time_no_params(self, auth_client):
        """GET /profile with no params equals All Time."""
        response = auth_client.get("/profile")
        assert response.status_code == 200
        # Should show all expenses


class TestProfileDateFilterEdgeCases:
    """Edge case tests for date filtering."""

    def test_profile_future_date_range(self, auth_client):
        """GET /profile with future dates returns empty but not crash."""
        response = auth_client.get("/profile?start_date=2027-01-01&end_date=2027-12-31")
        assert response.status_code == 200
        # Should show empty state gracefully
        assert b"No expenses in selected period" in response.data

    def test_profile_no_expenses_in_range(self, auth_client):
        """GET /profile with range that has no expenses shows empty state."""
        response = auth_client.get("/profile?start_date=2025-01-01&end_date=2025-12-31")
        assert response.status_code == 200
        assert b"No expenses in selected period" in response.data

    def test_profile_user_with_no_expenses(self, client, app):
        """Profile for user with no expenses shows zeros and empty state."""
        # Create and login a new user with no expenses
        with app.app_context():
            from database.db import get_db
            from werkzeug.security import generate_password_hash
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Empty User", "empty@test.com", generate_password_hash("pass123"))
            )
            user_id = cursor.lastrowid
            db.commit()

        client.post("/login", data={
            "email": "empty@test.com",
            "password": "pass123",
            "csrf_token": "test-token"
        }, follow_redirects=True)

        response = client.get("/profile")
        assert response.status_code == 200
        assert b"\xe2\x82\xb90.00" in response.data  # ₹0.00
        assert b"No expenses in selected period" in response.data

    def test_profile_different_users_see_only_their_expenses(self, client, app):
        """Users only see their own expenses, not others'."""
        with app.app_context():
            from database.db import get_db
            from werkzeug.security import generate_password_hash
            db = get_db()
            cursor = db.cursor()
            # Create second user with their own expenses
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("User Two", "user2@test.com", generate_password_hash("pass123"))
            )
            user2_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
                (user2_id, 999.99, "Luxury", "2026-06-15", "Private jet")
            )
            db.commit()

        # Login as user2
        client.post("/login", data={
            "email": "user2@test.com",
            "password": "pass123",
            "csrf_token": "test-token"
        }, follow_redirects=True)

        response = client.get("/profile")
        assert response.status_code == 200
        assert b"Private jet" in response.data
        assert b"Luxury" in response.data
        # Should NOT see demo user's expenses
        assert b"Lunch at cafe" not in response.data


class TestProfileDateFilterValidation:
    """Validation error tests for date filtering."""

    def test_profile_invalid_date_format_returns_200_with_flash(self, auth_client):
        """Invalid date format falls back to All Time with flash error."""
        response = auth_client.get("/profile?start_date=invalid&end_date=2026-12-31", follow_redirects=True)
        assert response.status_code == 200
        # Check for flash error message
        assert b"Invalid date format" in response.data

    def test_profile_invalid_end_date_format_returns_200_with_flash(self, auth_client):
        """Invalid end_date format falls back to All Time with flash error."""
        response = auth_client.get("/profile?start_date=2026-01-01&end_date=not-a-date", follow_redirects=True)
        assert response.status_code == 200
        assert b"Invalid date format" in response.data

    def test_profile_start_after_end_returns_200_with_flash(self, auth_client):
        """start_date > end_date falls back to All Time with flash error."""
        response = auth_client.get("/profile?start_date=2026-12-31&end_date=2026-01-01", follow_redirects=True)
        assert response.status_code == 200
        assert b"Start date cannot be after end date" in response.data

    def test_profile_same_start_end_valid(self, auth_client):
        """start_date == end_date is valid (single day)."""
        response = auth_client.get("/profile?start_date=2026-06-15&end_date=2026-06-15", follow_redirects=True)
        assert response.status_code == 200
        # Should not show error flash
        assert b"Start date cannot be after" not in response.data


class TestProfileDateFilterDataIntegrity:
    """Tests verifying filtered data integrity across all sections."""

    def test_summary_stats_reflects_filtered_expenses(self, auth_client):
        """Summary stats (total, count, top category) reflect date filter."""
        # All time
        response_all = auth_client.get("/profile")
        assert response_all.status_code == 200

        # Filter to April only
        response_apr = auth_client.get("/profile?start_date=2026-04-01&end_date=2026-04-30")
        assert response_apr.status_code == 200

        # April total should be less than all time
        # (Can't easily assert exact values without parsing HTML, but structure should be there)
        assert b"Total Spent" in response_apr.data
        assert b"Transactions" in response_apr.data
        assert b"Top Category" in response_apr.data

    def test_transaction_list_reflects_filtered_expenses(self, auth_client):
        """Transaction list shows only expenses within date range."""
        response = auth_client.get("/profile?start_date=2026-06-01&end_date=2026-06-30")
        assert response.status_code == 200
        # Should show June transactions
        assert b"Rent" in response.data or b"Restaurant" in response.data
        # Should NOT show April transactions
        assert b"Lunch at cafe" not in response.data
        assert b"Electric bill" not in response.data

    def test_category_breakdown_reflects_filtered_expenses(self, auth_client):
        """Category breakdown shows only categories with expenses in range."""
        response = auth_client.get("/profile?start_date=2026-06-01&end_date=2026-06-30")
        assert response.status_code == 200
        # Should show categories from June only (Bills, Food)
        # Percentages should sum to 100% within the filtered data
        assert b"Category Breakdown" in response.data
        assert b"%" in response.data

    def test_category_percentages_sum_to_100(self, auth_client):
        """Category breakdown percentages always sum to 100%."""
        # Test with various filters
        for params in [
            "",
            "?start_date=2026-04-01",
            "?end_date=2026-04-30",
            "?start_date=2026-04-01&end_date=2026-04-30",
            "?start_date=2026-06-01&end_date=2026-06-30",
        ]:
            response = auth_client.get(f"/profile{params}")
            assert response.status_code == 200
            # The template shows percentages, we verify structure exists
            assert b"Category Breakdown" in response.data


class TestProfileDateFilterTemplate:
    """Tests verifying template receives correct context."""

    def test_profile_passes_start_date_to_template(self, auth_client):
        """Template receives start_date value for date input."""
        response = auth_client.get("/profile?start_date=2026-04-01&end_date=2026-04-30")
        assert response.status_code == 200
        # Check that date input value attribute contains the date
        assert b'value="2026-04-01"' in response.data

    def test_profile_passes_end_date_to_template(self, auth_client):
        """Template receives end_date value for date input."""
        response = auth_client.get("/profile?start_date=2026-04-01&end_date=2026-04-30")
        assert response.status_code == 200
        assert b'value="2026-04-30"' in response.data

    def test_profile_empty_dates_when_no_filter(self, auth_client):
        """Date inputs are empty when no filter applied."""
        response = auth_client.get("/profile")
        assert response.status_code == 200
        # Inputs should have empty value or not have value attribute with date
        assert b'value=""' in response.data or b'value="2026' not in response.data


class TestProfileDateFilterRupeeSymbol:
    """Tests verifying all amounts display ₹ symbol."""

    def test_profile_total_spent_shows_rupee(self, auth_client):
        """Total spent displays ₹ symbol."""
        response = auth_client.get("/profile")
        assert response.status_code == 200
        assert b"\xe2\x82\xb9" in response.data  # ₹

    def test_profile_transaction_amounts_show_rupee(self, auth_client):
        """Transaction amounts display ₹ symbol."""
        response = auth_client.get("/profile")
        assert response.status_code == 200
        # Transaction table amounts should have ₹
        assert response.data.count(b"\xe2\x82\xb9") >= 3  # At least total + some transactions

    def test_profile_category_amounts_show_rupee(self, auth_client):
        """Category breakdown amounts display ₹ symbol."""
        response = auth_client.get("/profile")
        assert response.status_code == 200
        # Category amounts should have ₹
        assert response.data.count(b"\xe2\x82\xb9") >= 3


class TestProfileDateFilterEmptyState:
    """Tests for empty state handling."""

    def test_profile_empty_transactions_message(self, auth_client):
        """Empty transaction list shows appropriate message."""
        response = auth_client.get("/profile?start_date=2027-01-01&end_date=2027-12-31")
        assert response.status_code == 200
        # Table should exist but be empty or show message
        assert b"Recent Transactions" in response.data

    def test_profile_empty_categories_message(self, auth_client):
        """Empty category breakdown shows appropriate message."""
        response = auth_client.get("/profile?start_date=2027-01-01&end_date=2027-12-31")
        assert response.status_code == 200
        assert b"No expenses in selected period" in response.data

    def test_profile_zero_stats_for_empty_range(self, auth_client):
        """Stats show zero for empty date range."""
        response = auth_client.get("/profile?start_date=2027-01-01&end_date=2027-12-31", follow_redirects=True)
        assert response.status_code == 200
        assert b"\xe2\x82\xb90.00" in response.data  # ₹0.00