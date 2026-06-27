# Spec: Date Filter for Profile Page

## Overview
Step 6 adds date filtering capabilities to the profile page so users can view their expense summary, transaction list, and category breakdown for specific time periods. Users can select from preset ranges (This Month, Last Month, This Year, All Time) or define a custom date range. The filter applies to all four dynamic sections of the profile page — summary stats, transaction list, and category breakdown — giving users a focused view of their spending habits over any period.

## Depends on
- Step 1: Database setup (tables and `get_db()` exist)
- Step 2: Registration (users are stored in the database)
- Step 3: Login / Logout (`session["user_id"]` is set on login)
- Step 4: Profile page static UI (template already renders all four sections)
- Step 5: Backend routes for profile page (real DB queries replace hardcoded data)

## Routes
- `GET /profile` — modified to accept optional `start_date` and `end_date` query parameters — access level: logged-in

No new routes; the existing `/profile` route is extended with query parameters.

## Database changes
No database changes. The `expenses` table already has a `date` column in `YYYY-MM-DD` format.

## Templates
- **Modify**: `templates/profile.html`
  - Add a date filter bar above the summary stats row with:
    - Preset buttons: "This Month", "Last Month", "This Year", "All Time"
    - Custom date range inputs (two `<input type="date">` fields for start/end)
    - "Apply" button to submit the custom range
  - The filter bar should be styled using existing CSS variables
  - Preserve the current layout and visual hierarchy

## Files to change
- `app.py` — update the `profile()` view to parse `start_date` and `end_date` from query parameters, validate them, and pass them to query helpers
- `database/queries.py` — update all four query functions to accept optional `start_date` and `end_date` parameters and filter results accordingly
- `templates/profile.html` — add the date filter UI bar with preset buttons and custom range inputs

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never string-format values into SQL
- Foreign keys PRAGMA must be enabled on every connection (already done in `get_db()`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No inline styles
- Currency must always display as ₹ — never £ or $
- Date format for query parameters: `YYYY-MM-DD` (ISO 8601)
- Preset buttons should construct the correct date range client-side and redirect to `/profile?start_date=...&end_date=...`
- If `start_date` is provided without `end_date`, treat `end_date` as today
- If `end_date` is provided without `start_date`, treat `start_date` as the earliest expense date for that user
- If both are omitted, default to "All Time" (no date filtering)
- Invalid date formats or logically invalid ranges (start > end) should be ignored and fall back to "All Time" with a flash message
- All query helpers in `database/queries.py` must handle `None` dates gracefully (no filtering)
- Summary stats, transaction list, and category breakdown must all respect the same date filter

## Tests to write

### Unit tests
File: `tests/test_date_filter.py`

| Function | Input | Expected output |
|---|---|---|
| `get_summary_stats` | `user_id`, `start_date`, `end_date` covering 3 expenses | correct totals for only those 3 expenses |
| `get_summary_stats` | `user_id`, no dates | totals for all expenses (backward compatible) |
| `get_recent_transactions` | `user_id`, `start_date`, `end_date` | only transactions within range, newest-first |
| `get_category_breakdown` | `user_id`, `start_date`, `end_date` | categories only from expenses within range; pct sums to 100 |

### Route tests
`GET /profile` — authenticated with `start_date` and `end_date`:
- Returns 200
- Response contains only transactions within the date range
- Summary stats reflect only the filtered expenses
- Category breakdown reflects only the filtered expenses

`GET /profile` — authenticated with invalid date range (`start_date > end_date`):
- Returns 200 (falls back to All Time)
- Flash message indicates invalid range

`GET /profile` — preset button clicks (This Month, Last Month, This Year):
- Redirect to `/profile` with correct query parameters

## Definition of done
- [ ] Visiting `/profile` without query parameters shows all expenses (backward compatible)
- [ ] Clicking "This Month" shows only expenses from the current calendar month
- [ ] Clicking "Last Month" shows only expenses from the previous calendar month
- [ ] Clicking "This Year" shows only expenses from the current calendar year
- [ ] Clicking "All Time" clears filters and shows all expenses
- [ ] Entering a custom start/end date and clicking "Apply" shows only expenses within that range
- [ ] Summary stats (Total Spent, Transactions, Top Category) update to reflect the filtered data
- [ ] Transaction list shows only transactions within the selected range
- [ ] Category breakdown shows only categories with expenses in the selected range; percentages sum to 100%
- [ ] Invalid date range (start > end) falls back to All Time with a flash error message
- [ ] Date inputs display the currently selected range when filters are active
- [ ] All amounts continue to display with ₹ symbol