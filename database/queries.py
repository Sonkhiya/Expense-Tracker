"""Database query helpers for the profile page."""

from datetime import date
from database.db import get_db


def _build_date_filter(start_date: date | None, end_date: date | None):
    """Build WHERE clause and parameters for date filtering."""
    conditions = []
    params = []

    if start_date:
        conditions.append("date >= ?")
        params.append(start_date.isoformat())
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date.isoformat())

    where_clause = " AND ".join(conditions) if conditions else ""
    return where_clause, params


def get_user_by_id(user_id: int) -> dict | None:
    """Get user info by ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_summary_stats(user_id: int, start_date: date | None = None, end_date: date | None = None) -> dict:
    """Get summary stats for a user, optionally filtered by date range."""
    conn = get_db()
    cursor = conn.cursor()

    where_clause, params = _build_date_filter(start_date, end_date)
    if where_clause:
        where_clause = f"WHERE user_id = ? AND {where_clause}"
    else:
        where_clause = "WHERE user_id = ?"

    query_params = [user_id] + params

    # Total spent and transaction count
    cursor.execute(
        f"SELECT COALESCE(SUM(amount), 0) as total_spent, COUNT(*) as transaction_count "
        f"FROM expenses {where_clause}",
        query_params
    )
    row = cursor.fetchone()
    total_spent = row["total_spent"] if row else 0
    transaction_count = row["transaction_count"] if row else 0

    # Top category
    cursor.execute(
        f"""
        SELECT category, COALESCE(SUM(amount), 0) as category_total
        FROM expenses {where_clause}
        GROUP BY category
        ORDER BY category_total DESC
        LIMIT 1
        """,
        query_params
    )
    top_row = cursor.fetchone()
    top_category = top_row["category"] if top_row else "—"

    conn.close()

    return {
        "total_spent": f"₹{total_spent:,.2f}",
        "transaction_count": transaction_count,
        "top_category": top_category
    }


def get_recent_transactions(user_id: int, start_date: date | None = None, end_date: date | None = None, limit: int = 10) -> list[dict]:
    """Get recent transactions for a user, optionally filtered by date range, newest first."""
    conn = get_db()
    cursor = conn.cursor()

    where_clause, params = _build_date_filter(start_date, end_date)
    if where_clause:
        where_clause = f"WHERE user_id = ? AND {where_clause}"
    else:
        where_clause = "WHERE user_id = ?"

    query_params = [user_id] + params

    cursor.execute(
        f"""
        SELECT date, description, category, amount
        FROM expenses {where_clause}
        ORDER BY date DESC, id DESC
        LIMIT ?
        """,
        query_params + [limit]
    )
    rows = cursor.fetchall()
    conn.close()

    return [{"date": r["date"], "description": r["description"], "category": r["category"], "amount": f"₹{r['amount']:,.2f}"} for r in rows]


def get_category_breakdown(user_id: int, start_date: date | None = None, end_date: date | None = None) -> list[dict]:
    """Get category breakdown for a user, optionally filtered by date range."""
    conn = get_db()
    cursor = conn.cursor()

    where_clause, params = _build_date_filter(start_date, end_date)
    if where_clause:
        where_clause = f"WHERE user_id = ? AND {where_clause}"
    else:
        where_clause = "WHERE user_id = ?"

    query_params = [user_id] + params

    cursor.execute(
        f"""
        SELECT category, COALESCE(SUM(amount), 0) as category_total
        FROM expenses {where_clause}
        GROUP BY category
        ORDER BY category_total DESC
        """,
        query_params
    )
    rows = cursor.fetchall()

    # Calculate total for percentage
    total = sum(r["category_total"] for r in rows)

    if total == 0:
        conn.close()
        return []

    # Calculate percentages with rounding adjustment
    categories = []
    percentages = []
    for row in rows:
        cat_total = row["category_total"]
        pct = round((cat_total / total) * 100)
        percentages.append(pct)
        categories.append({"category": row["category"], "amount": cat_total, "pct": pct})

    # Adjust largest category to make percentages sum to 100
    current_sum = sum(percentages)
    if current_sum != 100 and categories:
        diff = 100 - current_sum
        categories[0]["pct"] += diff

    result = [
        {"name": c["category"], "amount": f"₹{c['amount']:,.2f}", "percentage": c["pct"], "pct": c["pct"]}
        for c in categories
    ]

    conn.close()
    return result