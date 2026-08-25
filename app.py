import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for

from database.db import create_user, get_db, init_db, seed_db, verify_user
from database.queries import (
    get_category_breakdown,
    get_recent_transactions,
    get_summary_stats,
    get_user_by_id,
)

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

    user_id = session["user_id"]

    member_row = get_user_by_id(user_id)
    if member_row is None:
        session.clear()
        flash("Please sign in again.", "error")
        return redirect(url_for("login"))

    member = {
        "name": member_row["name"],
        "email": member_row["email"],
        "member_since": member_row["member_since"],
    }

    # --- TODO(subagent-2: summary-stats) START ---
    summary = get_summary_stats(user_id)
    stats = [
        {"label": "Total spent", "value": f"₹{summary['total_spent']:.2f}", "note": "all time"},
        {"label": "Transactions", "value": str(summary["transaction_count"]), "note": "all time"},
        {
            "label": "Top category",
            "value": summary["top_category"],
            "note": (
                f"₹{summary['top_category_amount']:.2f} spent"
                if summary["transaction_count"] > 0 else "no expenses yet"
            ),
        },
    ]
    # --- TODO(subagent-2: summary-stats) END -----

    # --- TODO(subagent-1: transaction-history) START ---
    transactions = get_recent_transactions(user_id)
    # --- TODO(subagent-1: transaction-history) END -----

    # --- TODO(subagent-3: category-breakdown) START ---
    categories = get_category_breakdown(user_id)
    # --- TODO(subagent-3: category-breakdown) END -----

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
