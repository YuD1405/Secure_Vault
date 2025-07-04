from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from modules.auth.logic import register_user, process_login, get_user_by_email, update_user_info_in_db
from modules.auth.mfa import (verify_otp_code, verify_totp_code,
                              generate_and_send_otp, generate_qr_code, expire_otp_code)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('auth.dashboard'))
    
    if request.method == 'POST':
        email = request.form['email']
        passphrase = request.form['passphrase']
        result = process_login(email, passphrase)
        if result.get("success"):
            session['email'] = email
            session.pop('otp_sent', None)
            return redirect(url_for('auth.verify'))
        elif result.get("locked"):
            return render_template("login.html", locked=True)
        else:
            return render_template("login.html", error=result.get("message"))
    return render_template('login.html', error=None)

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

    selected_method = session.get("selected_method", "email")
    qr_code = generate_qr_code(email)

    # Gửi OTP qua mail khi GET lần đầu
    if request.method == 'GET' and 'otp_sent' not in session:
        generate_and_send_otp(email)
        session['otp_sent'] = True

    if request.method == 'POST':
        method = request.form.get('method')
        otp_input = request.form.get('otp')
        is_resend = request.form.get('resend')

        session['selected_method'] = method  # giữ lại tab

        if is_resend == '1' and method == 'email':
            generate_and_send_otp(email)
            flash("A new OTP has been sent to your email.", "success")
            return redirect(url_for('auth.verify'))

        if method == 'email':
            if verify_otp_code(email, otp_input):
                session.pop('otp_sent', None)
                session['user_id'] = email
                return redirect(url_for('auth.dashboard'))
            else:
                flash("Invalid or expired OTP", "email_error")

        elif method == 'totp':
            expire_otp_code(email)
            if verify_totp_code(email, otp_input):
                session.pop('otp_sent', None)
                session['user_id'] = email
                return redirect(url_for('auth.dashboard'))
            else:
                flash("Invalid TOTP code", "totp_error")

    return render_template("verify.html",
                           email=email,
                           qr_code=qr_code,
                           selected_method=session.get("selected_method", "email"))

@auth_bp.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    return render_template("user_dashboard.html", email=session.get("email"))

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@auth_bp.route("/recover_account")
def recover_account():
    return "Khôi phục account"

# Requirement 5 – update info
@auth_bp.route("/user_info")
def api_user_info():
    email = session.get("email")
    if not email:
        return jsonify({"error": "Not logged in"}), 401

    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user)

@auth_bp.route('/render_update_account', methods=['GET'])
def render_update_account():
    return render_template('update_account.html')

@auth_bp.route("/update_account", methods=["POST"])
def update_account():
    if 'email' not in session:
        return redirect(url_for('auth.login'))

    email = session['email']
    full_name = request.form.get('name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    dob = request.form.get('dob')
    pass1 = request.form.get('old_pass')
    pass2 = request.form.get('new_pass')

    success, message = update_user_info_in_db(email, full_name, phone, address, dob, pass1, pass2)

    return jsonify({"success": success, "message": message})
