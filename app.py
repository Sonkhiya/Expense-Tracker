import secrets
from datetime import datetime, date
from flask import Flask, render_template, request, session, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db
from database.queries import get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

# Initialize database on startup
with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # Redirect if already logged in
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "POST":
        # Validate CSRF token (skip in testing mode)
        if not app.config.get("TESTING", False):
            form_token = request.form.get("csrf_token")
            session_token = session.get("csrf_token")
            if not form_token or not session_token or form_token != session_token:
                flash("Invalid request. Please try again.", "error")
                return redirect(url_for("register"))

        # Extract form fields
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validation: all fields required
        if not name or not email or not password or not confirm_password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        # Validation: email format
        if "@" not in email or "." not in email.split("@")[-1]:
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("register"))

        # Validation: password minimum length
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return redirect(url_for("register"))

        # Validation: password match
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))

        # Check for duplicate email
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            flash("An account with this email already exists.", "error")
            return redirect(url_for("register"))

        # Insert new user
        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        conn.commit()
        conn.close()

        flash("Account created successfully! Please sign in.", "success")
        return redirect(url_for("login"))

    # GET request: generate CSRF token if not present
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)

    return render_template("register.html", csrf_token=session["csrf_token"])


@app.route("/login", methods=["GET", "POST"])
def login():
    # Redirect if already logged in
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "POST":
        # Validate CSRF token (skip in testing mode)
        if not app.config.get("TESTING", False):
            form_token = request.form.get("csrf_token")
            session_token = session.get("csrf_token")
            if not form_token or not session_token or form_token != session_token:
                flash("Invalid request. Please try again.", "error")
                return redirect(url_for("login"))

        # Extract form fields
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Validation: all fields required
        if not email or not password:
            flash("Please enter both email and password.", "error")
            return redirect(url_for("login"))

        # Validation: email format
        if "@" not in email or "." not in email.split("@")[-1]:
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("login"))

        # Query database for user
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        # Check if user exists and password is correct
        if not user or not check_password_hash(user[1], password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

        # Successful login: store user_id in session
        session["user_id"] = user[0]
        flash("Successfully signed in!", "success")
        return redirect(url_for("profile"))

    # GET request: generate CSRF token if not present
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)

    return render_template("login.html", csrf_token=session["csrf_token"])


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    # Authentication guard
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Parse and validate date query parameters
    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()

    start_date = None
    end_date = None
    date_error = None

    # Validate date format
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        date_error = "Invalid date format. Please use YYYY-MM-DD."

    # Validate logical validity
    if not date_error and start_date and end_date and start_date > end_date:
        date_error = "Start date cannot be after end date."

    # Handle edge cases for missing dates
    if not date_error:
        if start_date and not end_date:
            end_date = date.today()
        elif end_date and not start_date:
            # Get earliest expense date for this user
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT MIN(date) FROM expenses WHERE user_id = ?",
                (user_id,)
            )
            earliest = cursor.fetchone()[0]
            conn.close()
            if earliest:
                start_date = datetime.strptime(earliest, "%Y-%m-%d").date()

    # If date error, flash and fall back to All Time (no dates)
    if date_error:
        flash(date_error, "error")
        start_date = None
        end_date = None
        start_date_str = ""
        end_date_str = ""

    # Get user info
    user_data = get_user_by_id(user_id)
    if not user_data:
        session.clear()
        return redirect(url_for("login"))

    # Format member_since
    try:
        created_at = datetime.strptime(user_data["created_at"], "%Y-%m-%d %H:%M:%S")
        member_since = created_at.strftime("%B %Y")
    except (ValueError, TypeError):
        member_since = "Unknown"

    # Get initials
    name_parts = user_data["name"].split()
    initials = "".join([p[0].upper() for p in name_parts[:2]]) if name_parts else "U"

    # Get filtered data
    stats = get_summary_stats(user_id, start_date, end_date)
    transactions = get_recent_transactions(user_id, start_date, end_date, limit=50)
    categories = get_category_breakdown(user_id, start_date, end_date)

    context = {
        "user": {
            "name": user_data["name"],
            "email": user_data["email"],
            "member_since": member_since,
            "initials": initials
        },
        "stats": stats,
        "transactions": transactions,
        "categories": categories,
        "start_date": start_date_str,
        "end_date": end_date_str
    }

    return render_template("profile.html", **context)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5002)
