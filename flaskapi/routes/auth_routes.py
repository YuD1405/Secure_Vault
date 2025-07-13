from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from modules.auth.logic import register_user, process_login, get_user_by_email, update_user_info_in_db, verify_recovery_code_from_db, reset_password_and_update_recovery_code_in_db, get_salt_from_db
from modules.auth.mfa import (verify_otp_code, verify_totp_code,
                              generate_and_send_otp, generate_qr_code, expire_otp_code)
from modules.utils.logger import read_security_logs, log_user_action
from modules.utils.manage_account import fetch_all_users, toggle_user_lock
from modules.crypto.key_management import re_encrypt_private_key_with_new_passphrase, reencrypt_private_key_after_recovery, derive_aes_key, check_and_manage_own_keys
from modules.auth.validator import sanitize_input

auth_bp = Blueprint('auth', __name__)

# Requirement 1 – Sign up
@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        success, message, recovery_code = register_user(request.form)
        email = sanitize_input(request.form.get("email", ""))
        if success:
            # Gọi hàm check_and_manage_own_keys để tạo khóa đầu tiên (thêm parementer recovery code)
            log_user_action(email, "Register", "Success", message)
            return render_template("signup.html", success=message, recovery_code=recovery_code)
        else:
            log_user_action(email, "Register", "Fail", message, 'error')
            return render_template("signup.html", error=message)
    return render_template("signup.html")


# Requirement 2 - Log in - MFA
# Requirement 15 - Limit login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('auth.dashboard'))
    
    if request.method == 'POST':
        email = request.form['email']
        passphrase = request.form['passphrase']
        result = process_login(email, passphrase)
        salt = get_salt_from_db(email)
        if result.get("success"):
            aes_key = derive_aes_key(passphrase, get_salt_from_db(email))
            check_and_manage_own_keys(email, passphrase, aes_key, salt)
    
            session['passphrase'] = passphrase
            session['email'] = email
            session['role'] = result.get("role")
            session.pop('otp_sent', None)
            log_user_action(email, "Login", "Success", "Login successfully")
            return redirect(url_for('auth.verify'))
        elif result.get("locked_by_admin"):
            log_user_action(email, "Login", "Fail", "Account locked by admin")
            return render_template("login.html", locked_by_admin=True)
        elif result.get("locked"):
            log_user_action(email, "Login", "Fail", "Account locked")
            return render_template("login.html", locked=True)
        else:
            log_user_action(email, "Login", "Fail", result.get("message"))
            return render_template("login.html", error=result.get("message"))
    return render_template('login.html', error=None)

@auth_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    email = session.get('email')
    if not email:
        flash("Session expired. Please login again.", "error")
        log_user_action("Unknown", "MFA Verify", "Fail", "Session expired", level="warning")
        return redirect(url_for('auth.login'))

    selected_method = session.get("selected_method", "email")
    qr_code = generate_qr_code(email)

    # Gửi OTP qua mail khi GET lần đầu
    if request.method == 'GET' and 'otp_sent' not in session:
        generate_and_send_otp(email)
        session['otp_sent'] = True
        log_user_action(email, "Send OTP", "Success", "OTP sent via email")

    if request.method == 'POST':
        method = request.form.get('method')
        otp_input = request.form.get('otp')
        is_resend = request.form.get('resend')

        session['selected_method'] = method  # giữ lại tab

        if is_resend == '1' and method == 'email':
            generate_and_send_otp(email)
            flash("A new OTP has been sent to your email.", "success")
            log_user_action(email, "Resend OTP", "Success")
            return redirect(url_for('auth.verify'))

        if method == 'email':
            if verify_otp_code(email, otp_input):
                session.pop('otp_sent', None)
                session['user_id'] = email
                log_user_action(email, "OTP Verify", "Success")
                if session.get("role") == "admin":
                    return redirect(url_for("auth.admin_dashboard"))
                return redirect(url_for('auth.dashboard'))
            else:
                flash("Invalid or expired OTP", "email_error")
                log_user_action(email, "OTP Verify", "Fail", "Invalid or expired OTP", level="warning")

        elif method == 'totp':
            expire_otp_code(email)
            if verify_totp_code(email, otp_input):
                session.pop('otp_sent', None)
                session['user_id'] = email
                log_user_action(email, "TOTP Verify", "Success")
                if session.get("role") == "admin":
                    return redirect(url_for("auth.admin_dashboard"))
                return redirect(url_for('auth.dashboard'))
            else:
                flash("Invalid TOTP code", "totp_error")
                log_user_action(email, "TOTP Verify", "Fail", "Wrong 6-digit TOTP", level="warning")

    return render_template("verify.html",
                           email=email,
                           qr_code=qr_code,
                           selected_method=session.get("selected_method", "email"))

@auth_bp.route("/logout")
def logout():
    email = session.get("email", "Unknown")
    log_user_action(email, "Logout","Success", "Logout successfully")
    session.clear()
    return redirect(url_for("auth.login"))


# Requirement 10 - Divide roles
@auth_bp.route("/dashboard")
def dashboard():    
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    
    return render_template("user_dashboard.html", email=session.get("email"))

@auth_bp.route("/admin_dashboard")
def admin_dashboard():
    if not session.get("user_id") and session.get("role") != "admin":
        flash("Access denied.", "error")
        return redirect(url_for("auth.login"))
    
    logs = read_security_logs()
    return render_template("admin_dashboard.html", email=session.get("email"), logs=logs)

@auth_bp.route("/admin_manage_account", methods=['GET', 'POST'])
def admin_manage_account():
    if not session.get("user_id") and session.get("role") != "admin":
        flash("Access denied.", "error")
        return redirect(url_for("auth.login"))
    
    if request.method == "POST":
        email = request.form.get("email")
        action = request.form.get("action")  # "lock" hoặc "unlock"
        toggle_user_lock(email, lock=(action == "lock"))

    users = fetch_all_users()
    return render_template("admin_manage_account.html", email=session.get("email"), users=users)


# Requirement 17 – update info
@auth_bp.route("/recover_account")
def render_recover_account():
    return render_template("recover_account.html")

@auth_bp.route('/verify_recovery', methods=['POST'])
def verify_recovery_code():
    data = request.get_json()
    email = data.get('email')
    recovery_code = data.get('recovery_code')

    success, error = verify_recovery_code_from_db(email, recovery_code)

    if success:
        session["recovery_verified"] = True
        session["recovery_email"] = email
        log_user_action(email, "Verify Recovery Code", "Success","Recovery code matched. Proceed to password reset.")
        return jsonify({'success': True})
    else:
        log_user_action(email, "Verify Recovery Code", "Fail", error, level="warning")
        return jsonify({'success': False, 'message': error}), 400
    
@auth_bp.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('new_password')
    
    if not session.get("recovery_verified"):
        return jsonify({"success": False, "message": "Recovery session expired"}), 401

    # --- Bước 1: cập nhật mật khẩu + recovery code mã hóa ---
    success, error = reset_password_and_update_recovery_code_in_db(email, new_password)
    if not success:
        log_user_action(email, "Reset Password", "Fail", error or "DB update failed", level="error")
        return jsonify({'success': False, 'message': error or 'Failed to reset password'}), 400

    # --- Bước 2: Mã hóa lại private key ---
    success_key, msg = reencrypt_private_key_after_recovery(email, new_password)
    if not success_key:
        log_user_action(email, "Reset Password", "Fail", f"Re-encrypt RSA failed: {msg}", level="error")
        return jsonify({'success': False, 'message': msg})

    # --- Cập nhật session ---
    session["passphrase"] = new_password
    session.pop("recovery_verified", None)
    session.pop("recovery_email", None)

    log_user_action(email, "Reset Password", "Success", "New passphrase and private key updated successfully.")
    return jsonify({'success': True})


# Requirement 5 – update info
@auth_bp.route("/user_info")
def api_user_info():
    email = session.get("email")
    if not email:
        log_user_action(email, "Get User Info", "Fail", "Not logged in", level="warning")
        return jsonify({"error": "Not logged in"}), 401

    user = get_user_by_email(email)
    if not user:
        log_user_action(email, "Get User Info", "Fail", "User not found", level="warning")
        return jsonify({"error": "User not found"}), 404

    log_user_action(email, "Get User Info", "Success", "User profile returned")
    return jsonify(user)

@auth_bp.route('/render_update_account', methods=['GET'])
def render_update_account():
    return render_template('update_account.html')

@auth_bp.route("/update_account", methods=["POST"])
def update_account():
    if 'email' not in session:
        log_user_action("Unknown", "Update Account", "Fail", "No session", level="warning")
        return redirect(url_for('auth.login'))

    email = session['email']
    full_name = request.form.get('name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    dob = request.form.get('dob')
    pass1 = request.form.get('old_pass')
    pass2 = request.form.get('new_pass')
    
    success, message = update_user_info_in_db(email, full_name, phone, address, dob, pass1, pass2)
    if success:
        log_user_action(email, "Update Account Info", "Success", "User info updated")
        if(pass1 and pass2):
            success_1, msg1 = re_encrypt_private_key_with_new_passphrase(email, pass1, pass2)
            if success_1 == False:
                log_user_action(email, "Change Passphrase", "Fail", f"RSA re-encryption failed: {msg1}", level="error")
                return jsonify({'success': False, 'message': msg1})
            session["passphrase"] = pass2
    else:
        log_user_action(email, "Update Account Info", "Fail", message or "Unknown error", level="warning")

    return jsonify({"success": success, "message": message})
