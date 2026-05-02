import secrets
from flask import Flask, render_template, request, session, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db

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
        # Validate CSRF token
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
        # Validate CSRF token
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

    # Hardcoded context data for UI design
    context = {
        "user": {
            "name": "Demo User",
            "email": "demo@spendly.com",
            "member_since": "January 15, 2024",
            "initials": "DU"
        },
        "stats": {
            "total_spent": "₹12,450.00",
            "transaction_count": 24,
            "top_category": "Food"
        },
        "transactions": [
            {"date": "2024-01-28", "description": "Grocery shopping", "category": "Food", "amount": "₹2,450.00"},
            {"date": "2024-01-27", "description": "Uber ride", "category": "Transport", "amount": "₹350.00"},
            {"date": "2024-01-26", "description": "Electricity bill", "category": "Bills", "amount": "₹1,200.00"},
            {"date": "2024-01-25", "description": "Movie tickets", "category": "Entertainment", "amount": "₹800.00"},
            {"date": "2024-01-24", "description": "Online shopping", "category": "Shopping", "amount": "₹1,500.00"}
        ],
        "categories": [
            {"name": "Food", "amount": "₹5,200.00", "percentage": 42},
            {"name": "Transport", "amount": "₹3,100.00", "percentage": 25},
            {"name": "Bills", "amount": "₹2,800.00", "percentage": 22},
            {"name": "Entertainment", "amount": "₹1,350.00", "percentage": 11}
        ]
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
