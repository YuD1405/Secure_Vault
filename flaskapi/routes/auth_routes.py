from flask import Blueprint, render_template, request, redirect, url_for, session, flash, get_flashed_messages
import hashlib
from modules.auth.logic import register_user, process_login
from modules.auth.mfa import verify_otp_code, verify_totp_code, generate_and_send_otp, generate_qr_code, expire_otp_code
from flaskapi.extensions import mysql
import time
# from modules.auth.mfa_totp import get_totp_uri, generate_qr_base64
# from modules.auth.mfa_otp import generate_otp, validate_otp, send_otp_via_email

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        passphrase = request.form['passphrase']
        result = process_login(email, passphrase)
        if result.get("success"):
            session['email'] = email  # lưu email để gửi OTP
            return redirect(url_for('auth.verify'))  # chuyển hướng đến trang xác thực OTP
        elif result.get("locked"):
            return render_template("login.html", locked=True)
        else:
            return render_template("login.html", error=result.get("message"))
    return render_template('login.html',error = None)

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        success, message, recovery_code = register_user(request.form)
        if success:
            return render_template("signup.html", success=message, recovery_code=recovery_code)
        else:
            return render_template("signup.html", error=message)
    return render_template("signup.html")


@auth_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    email = session.get('email')
    if not email:
        flash("Session expired. Please login again.", "error")
        return redirect(url_for('auth.login'))

    qr_code = generate_qr_code(email)

    # Mặc định gửi OTP nếu vừa vào lần đầu
    if request.method == 'GET':
        generate_and_send_otp(email)

    # Xử lý POST: xác minh OTP/TOTP
    if request.method == 'POST':
        method = request.form.get('method')  # email hoặc totp
        otp_input = request.form.get('otp')

        if method == 'email':
            if verify_otp_code(email, otp_input):
                session['user_id'] = email
                return redirect(url_for('auth.dashboard'))
            else:
                flash("Invalid or expired OTP", "error")
        elif method == 'totp':
            expire_otp_code(email)  # ⚠️ Hủy hiệu lực OTP nếu chọn TOTP
            if verify_totp_code(email, otp_input):
                session['user_id'] = email
                return redirect(url_for('auth.dashboard'))
            else:
                flash("Invalid TOTP code", "error")

    return render_template("verify.html", email=email, qr_code=qr_code)




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