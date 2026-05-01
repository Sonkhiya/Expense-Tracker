import sqlite3
import random
from datetime import datetime
from werkzeug.security import generate_password_hash

DATABASE = "spendly.db"

# Common Indian first names across regions
FIRST_NAMES = [
    "Aarav", "Vihaan", "Aditya", "Arjun", "Rohan", "Aryan", "Ishaan", "Karan",
    "Priya", "Ananya", "Diya", "Sneha", "Meera", "Kavya", "Riya", "Neha",
    "Rahul", "Amit", "Vikram", "Sanjay", "Rajesh", "Suresh", "Deepak", "Manoj",
    "Pooja", "Sunita", "Anita", "Geeta", "Sharma", "Verma", "Patel", "Singh",
    "Arjun", "Kartik", "Siddharth", "Abhishek", "Nikhil", "Akash", "Pradeep",
    "Anjali", "Divya", "Preeti", "Swati", "Nisha", "Pallavi", "Shruti", "Tanya"
]

# Common Indian last names across regions
LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Singh", "Kumar", "Gupta", "Agarwal", "Malhotra",
    "Reddy", "Nair", "Iyer", "Rao", "Menon", "Pillai", "Krishnan", "Subramaniam",
    "Chatterjee", "Banerjee", "Mukherjee", "Ganguly", "Das", "Bose", "Sengupta",
    "Desai", "Joshi", "Kulkarni", "Patil", "Shinde", "Jadhav", "Deshmukh",
    "Mehta", "Shah", "Kapoor", "Sethi", "Khanna", "Bhatia", "Bhatt", "Trivedi",
    "Pandey", "Tiwari", "Mishra", "Srivastava", "Sinha", "Thakur", "Yadav"
]

def get_db():
    """Open connection to SQLite database with row_factory and foreign keys enabled."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def generate_indian_name():
    """Generate a realistic Indian name."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    return f"{first_name} {last_name}"

def generate_email(name):
    """Generate email from name with random 2-3 digit suffix."""
    parts = name.lower().split()
    first = parts[0]
    last = parts[1] if len(parts) > 1 else "user"
    digits = random.randint(10, 999)
    return f"{first}.{last}{digits}@gmail.com"

def email_exists(email):
    """Check if email already exists in database."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def create_unique_user():
    """Generate a unique user that doesn't exist in database."""
    max_attempts = 50
    for _ in range(max_attempts):
        name = generate_indian_name()
        email = generate_email(name)
        if not email_exists(email):
            return name, email
    raise Exception(f"Could not generate unique email after {max_attempts} attempts")

def main():
    # Initialize database tables if not exists
    from database.db import init_db
    init_db()

    # Generate unique user
    name, email = create_unique_user()
    password_hash = generate_password_hash("password123")
    created_at = datetime.now().isoformat()

    # Insert into database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (name, email, password_hash, created_at)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    # Print confirmation
    print(f"User created successfully!")
    print(f"  id: {user_id}")
    print(f"  name: {name}")
    print(f"  email: {email}")

if __name__ == "__main__":
    main()
