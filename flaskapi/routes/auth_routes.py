from flask import Blueprint, render_template, request, redirect, url_for, session
import hashlib
from modules.auth.logic import register_user
from flaskapi.extensions import mysql 

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
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
            return redirect(url_for("auth.dashboard"))
        else:
            return render_template("login.html", error="Sai email hoặc passphrase")
    return render_template("login.html")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        success, message = register_user(request.form)
        if success:
            return render_template("login.html", success=message)
        else:
            return render_template("signup.html", error=message)
    return render_template("signup.html")


@auth_bp.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    return "Đây là dashboard người dùng"


@auth_bp.route("/logout")
def logout():
    #session.clear()
    return redirect(url_for("auth.login"))

@auth_bp.route("/recover_account")
def recover_account():
    return "Khôi phục account"

@auth_bp.route("/update_account")
def update_account():
    return "Upd account"