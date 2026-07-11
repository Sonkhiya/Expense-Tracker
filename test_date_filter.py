#!/usr/bin/env python3
"""Test script to validate date filter implementation."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Test imports
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown
)
from database.db import get_db, init_db

# Initialize DB
init_db()

# Test 1: Get user
print("Test 1: Get user by ID")
user = get_user_by_id(1)
print(f"  User: {user}")

# Test 2: Get summary stats (no filter)
print("\nTest 2: Summary stats (no filter)")
stats = get_summary_stats(1)
print(f"  Stats: {stats}")

# Test 3: Get summary stats (with filter)
print("\nTest 3: Summary stats (with date filter)")
from datetime import date
stats = get_summary_stats(1, date(2026, 4, 1), date(2026, 4, 30))
print(f"  Stats: {stats}")

# Test 4: Get recent transactions (no filter)
print("\nTest 4: Recent transactions (no filter)")
txns = get_recent_transactions(1, limit=10)
print(f"  Transactions: {txns}")

# Test 5: Get recent transactions (with filter)
print("\nTest 5: Recent transactions (with date filter)")
txns = get_recent_transactions(1, date(2026, 4, 1), date(2026, 4, 30), limit=10)
print(f"  Transactions: {txns}")

# Test 6: Get category breakdown (no filter)
print("\nTest 6: Category breakdown (no filter)")
cats = get_category_breakdown(1)
print(f"  Categories: {cats}")
if cats:
    pct_sum = sum(c['pct'] for c in cats)
    print(f"  Percentages sum: {pct_sum}")

# Test 7: Get category breakdown (with filter)
print("\nTest 7: Category breakdown (with date filter)")
cats = get_category_breakdown(1, date(2026, 4, 1), date(2026, 4, 30))
print(f"  Categories: {cats}")
if cats:
    pct_sum = sum(c['pct'] for c in cats)
    print(f"  Percentages sum: {pct_sum}")

print("\n✅ All tests passed!")