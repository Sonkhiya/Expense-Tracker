#!/usr/bin/env python3
"""Seed realistic dummy expenses for a specific user."""

import sys
import random
from datetime import datetime, timedelta
from database.db import get_db

# Category configurations with Indian context
CATEGORIES = {
    "Food": {
        "min": 50,
        "max": 800,
        "weight": 25,
        "descriptions": [
            "Lunch at local restaurant",
            "Street food and snacks",
            "Family dinner at home",
            "Order from Swiggy",
            "Breakfast at cafe",
            "Groceries from market",
            "Office tiffin service",
            "Weekend biryani",
            "Chai and samosa",
            "South Indian thali",
        ],
    },
    "Transport": {
        "min": 20,
        "max": 500,
        "weight": 15,
        "descriptions": [
            "Auto rickshaw fare",
            "Metro card recharge",
            "Uber/Ola ride",
            "Bus pass monthly",
            "Petrol refill",
            "Train ticket",
            "Bike maintenance",
            "Airport cab",
        ],
    },
    "Bills": {
        "min": 200,
        "max": 3000,
        "weight": 12,
        "descriptions": [
            "Electricity bill",
            "Mobile postpaid bill",
            "Internet broadband",
            "Water bill",
            "Cooking gas refill",
            "Society maintenance",
            "DTH recharge",
            "Property tax",
        ],
    },
    "Health": {
        "min": 100,
        "max": 2000,
        "weight": 8,
        "descriptions": [
            "Doctor consultation",
            "Medicines from pharmacy",
            "Health checkup",
            "Dental visit",
            "Eye test and glasses",
            "Gym membership",
            "Ayurvedic medicines",
            "Physiotherapy session",
        ],
    },
    "Entertainment": {
        "min": 100,
        "max": 1500,
        "weight": 10,
        "descriptions": [
            "Movie tickets PVR/INOX",
            "Netflix subscription",
            "Hotstar premium",
            "Weekend outing",
            "Concert tickets",
            "Gaming subscription",
            "Amusement park visit",
            "Spotify premium",
        ],
    },
    "Shopping": {
        "min": 200,
        "max": 5000,
        "weight": 18,
        "descriptions": [
            "New clothes from mall",
            "Amazon online order",
            "Flipkart big billion",
            "Festival shopping",
            "Shoes and footwear",
            "Watch accessory",
            "Home decor items",
            "Electronics gadget",
            "Jewelry purchase",
            "Myntra fashion",
        ],
    },
    "Other": {
        "min": 50,
        "max": 1000,
        "weight": 7,
        "descriptions": [
            "Gift for friend",
            "Donation to temple",
            "Stationery items",
            "Pet supplies",
            "Car wash",
            "Laundry service",
            "Salon visit",
            "Miscellaneous expense",
        ],
    },
}


def parse_args():
    """Parse command line arguments."""
    if len(sys.argv) != 4:
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        sys.exit(1)

    try:
        user_id = int(sys.argv[1])
        count = int(sys.argv[2])
        months = int(sys.argv[3])
        return user_id, count, months
    except ValueError:
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        print("Error: All arguments must be valid integers.")
        sys.exit(1)


def verify_user(user_id):
    """Verify that the user exists in the database."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user is None:
        print(f"No user found with id {user_id}.")
        sys.exit(1)

    return user


def select_category():
    """Select a category based on weights (Food most common, Health/Other least)."""
    categories = list(CATEGORIES.keys())
    weights = [CATEGORIES[cat]["weight"] for cat in categories]
    return random.choices(categories, weights=weights)[0]


def generate_amount(category):
    """Generate a realistic amount for the given category."""
    min_amt = CATEGORIES[category]["min"]
    max_amt = CATEGORIES[category]["max"]
    amount = round(random.uniform(min_amt, max_amt), 2)
    # Round to nearest 5 or 10 for realistic Indian amounts
    if amount < 100:
        return round(amount / 5) * 5
    return round(amount / 50) * 50


def generate_description(category):
    """Generate a realistic description for the category."""
    return random.choice(CATEGORIES[category]["descriptions"])


def generate_date(start_date, end_date):
    """Generate a random date between start and end."""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)


def generate_expenses(user_id, count, months):
    """Generate a list of expense tuples."""
    today = datetime.now()
    start_date = today - timedelta(days=months * 30)
    end_date = today

    expenses = []
    for _ in range(count):
        category = select_category()
        amount = generate_amount(category)
        description = generate_description(category)
        date = generate_date(start_date, end_date)

        expenses.append(
            (user_id, amount, category, date.strftime("%Y-%m-%d"), description)
        )

    # Sort by date for realistic ordering
    expenses.sort(key=lambda x: x[3])

    return expenses, start_date, end_date


def insert_expenses(expenses):
    """Insert all expenses in a single transaction."""
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            expenses,
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error inserting expenses: {e}")
        conn.close()
        sys.exit(1)
    finally:
        conn.close()


def print_confirmation(count, start_date, end_date, expenses):
    """Print confirmation with sample records."""
    print(f"\nSuccessfully inserted {count} expenses.")
    print(
        f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )
    print("\nSample records (first 5):")
    print("-" * 80)

    for i, exp in enumerate(expenses[:5]):
        user_id, amount, category, date, description = exp
        print(f"{i+1}. [{date}] {category}: ₹{amount:.2f} - {description}")

    print("-" * 80)


def main():
    user_id, count, months = parse_args()

    # Verify user exists
    user = verify_user(user_id)
    print(f"Seeding {count} expenses for user '{user['name']}' (ID: {user_id})...")

    # Generate expenses
    expenses, start_date, end_date = generate_expenses(user_id, count, months)

    # Insert expenses
    insert_expenses(expenses)

    # Print confirmation
    print_confirmation(count, start_date, end_date, expenses)


if __name__ == "__main__":
    main()
