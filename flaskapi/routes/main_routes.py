from flask import Blueprint, render_template, request, redirect, url_for, session
from flaskapi.app import mysql
import hashlib
from modules.auth.logic import register_user

main_routes = Blueprint("main", __name__)


@main_routes.route("/")
def home():
    if session.get("user_id"):
        return redirect("/dashboard")
    return redirect("/login")


@main_routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        passphrase = request.form["passphrase"]
        hashed = hashlib.sha256(passphrase.encode()).hexdigest()

        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT id FROM users WHERE email=%s AND passphrase=%s",
            (email, hashed)
        )
        user = cur.fetchone()
        cur.close()

        if user:
            session["user_id"] = user[0]
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Sai email hoặc passphrase")
    return render_template("login.html")


@main_routes.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        success, message = register_user(request.form)
        if success:
            return render_template("signup.html", success=message)
        else:
            return render_template("signup.html", error=message)
    return render_template("signup.html")


@main_routes.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect("/login")
    return "Đây là dashboard người dùng"


@main_routes.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
