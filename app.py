import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for

from database.db import create_user, get_db, init_db, seed_db, verify_user

app = Flask(__name__)

# Dev-only secret — flash() needs a signed session.
# Move to an environment variable before deploying anywhere real.
app.secret_key = "dev-secret-key-change-me"

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
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        error = None
        if not name or not email or not password or not confirm_password:
            error = "All fields are required."
        elif "@" not in email:
            error = "Enter a valid email address."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm_password:
            error = "Passwords do not match."

        if error is None:
            try:
                create_user(name, email, password)
            except sqlite3.IntegrityError:
                error = "An account with this email already exists."

        if error is not None:
            flash(error, "error")
            return render_template("register.html"), 400

        flash("Account created. Please sign in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        error = None
        user = None
        if not email or not password:
            error = "Email and password are required."
        else:
            user = verify_user(email, password)
            if user is None:
                # Same message whether the email is unknown or the password is
                # wrong — never confirm which accounts exist.
                error = "Invalid email or password."

        if error is not None:
            flash(error, "error")
            return render_template("login.html"), 400

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("profile"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("landing"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    member = {
        "name": session.get("user_name", "Member"),
        "email": "demo@spendly.com",
        "member_since": "March 2024",
    }

    stats = [
        {"label": "Total spent", "value": "₹18,240", "note": "this month"},
        {"label": "Transactions", "value": "34", "note": "this month"},
        {"label": "Top category", "value": "Food", "note": "₹6,120 spent"},
    ]

    transactions = [
        {"date": "2026-08-03", "description": "Groceries", "category": "Food", "amount": 25.50},
        {"date": "2026-08-02", "description": "Bus pass", "category": "Transport", "amount": 12.00},
        {"date": "2026-08-01", "description": "Electricity bill", "category": "Bills", "amount": 60.00},
        {"date": "2026-07-31", "description": "Pharmacy", "category": "Health", "amount": 45.00},
        {"date": "2026-07-30", "description": "Movie ticket", "category": "Entertainment", "amount": 15.00},
    ]

    categories = [
        {"name": "Food", "amount": 6120, "percent": 78},
        {"name": "Transport", "amount": 3480, "percent": 58},
        {"name": "Bills", "amount": 2880, "percent": 48},
        {"name": "Health", "amount": 1950, "percent": 32},
        {"name": "Entertainment", "amount": 1200, "percent": 20},
        {"name": "Shopping", "amount": 1740, "percent": 28},
        {"name": "Other", "amount": 870, "percent": 14},
    ]

    return render_template(
        "profile.html",
        member=member,
        stats=stats,
        transactions=transactions,
        categories=categories,
    )


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
    app.run(debug=True, port=5001)
