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
        flash("Welcome back!", "success")
        return redirect(url_for("landing"))

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
    return "Profile page — coming in Step 4"


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
