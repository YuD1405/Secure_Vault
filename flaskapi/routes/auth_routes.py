from flask import Blueprint, render_template, request, redirect, url_for, session
import hashlib
from modules.auth.logic import register_user, process_login
from flaskapi.extensions import mysql 
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
            # session['pre_otp_email'] = email
            # return redirect(url_for('auth.verify'))
            return redirect(url_for('auth.dashboard'))
        else:
            return render_template('login.html', error=result.get("message"))
    return render_template('login.html')

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        success, message, recovery_code = register_user(request.form)
        if success:
            return render_template("signup.html", success=message, recovery_code=recovery_code)
        else:
            return render_template("signup.html", error=message)
    return render_template("signup.html")


# @auth_bp.route('/verify', methods=['GET', 'POST'])
# def verify():
#     email = session.get("pre_otp_email")
#     if not email:
#         return redirect(url_for('auth.login'))

#     # gửi OTP nếu chưa có
    
#     otp = generate_otp(email)
#     send_otp_via_email(email, otp)  # bạn cần viết hàm này (SMTP)
#     session['otp_attempt'] = 0

#     return render_template("verify.html", email=email, qr_code="")


# @auth_bp.route('/generate_totp', methods=['POST'])
# def generate_totp():
#     email = session.get("pre_otp_email")
    
#     # bạn cần tạo hàm này để lấy mfa_secret từ DB
#     from database import get_user_secret
#     secret = get_user_secret(email)
#     uri = get_totp_uri(email, secret)
#     qr = generate_qr_base64(uri)
#     return render_template("verify.html", email=email, qr_code=qr)


# @auth_bp.route('/verify_otp', methods=['POST'])
# def verify_otp():
#     otp = request.form.get('otp')
#     email = session.get("pre_otp_email")
#     if validate_otp(email, otp):
#         session['user_email'] = email
#         return redirect(url_for('dashboard.index'))
#     else:
#         flash("Invalid or expired OTP")
#         return redirect(url_for('auth.verify'))


# @auth_bp.route('/verify_totp', methods=['POST'])
# def verify_totp():
#     from database import get_user_secret
#     import pyotp
#     email = session.get("pre_otp_email")
#     secret = get_user_secret(email)
#     totp = pyotp.TOTP(secret)
#     otp = request.form.get("otp")
#     session['otp_attempt'] += 1
#     if session['otp_attempt'] >= 5:
#         lock_user(email)
#         flash("Too many failed attempts. Account locked.")
#         return redirect(url_for('auth.login'))

#     if totp.verify(otp):
#         session['user_email'] = email
#         return redirect(url_for('dashboard.index'))
#     else:
#         flash("Incorrect TOTP. Try again.")
#         return redirect(url_for('auth.verify'))


# @auth_bp.route('/resend_otp', methods=['POST'])
# def resend_otp():
#     email = session.get("pre_otp_email")
#     from modules.mfa_otp import generate_otp
#     otp = generate_otp(email)
#     send_otp_via_email(email, otp)
#     flash("OTP resent.")
#     return redirect(url_for('auth.verify'))

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