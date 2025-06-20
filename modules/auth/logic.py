from flaskapi.extensions import mysql
from modules.auth.validator import (
    is_valid_email, is_valid_date, is_valid_phone,
    is_strong_passphrase, sanitize_input
)
from modules.utils.logger import log_user_action
import os
import random
import string
import hashlib
import pyotp
from datetime import datetime, timedelta


def generate_salt(length=16):
    return os.urandom(length).hex()


def hash_with_salt(passphrase, salt):
    return hashlib.sha256((passphrase + salt).encode()).hexdigest()


def generate_recovery_code(length=12):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def register_user(data: dict) -> tuple:
    email = sanitize_input(data.get("email", ""))
    name = sanitize_input(data.get("name", ""))
    dob = sanitize_input(data.get("dob", ""))
    phone = sanitize_input(data.get("phone", ""))
    address = sanitize_input(data.get("address", ""))
    pass1 = data.get("passphrase", "")
    pass2 = data.get("repeat_passphrase", "")

    if not all([email, name, dob, phone, address, pass1, pass2]):
        return False, "All fields are required.", None
    if not is_valid_email(email):
        return False, "Invalid email format.", None
    if not is_valid_date(dob):
        return False, "Invalid date format.", None
    if not is_valid_phone(phone):
        return False, "Phone must be 10 digits.", None
    if not is_strong_passphrase(pass1):
        return False, "Passphrase too weak (min 8 chars, upper, digit, symbol).", None
    if pass1 != pass2:
        return False, "Passphrases do not match.", None

    salt = generate_salt()
    hashed = hash_with_salt(pass1, salt)
    recovery_code = generate_recovery_code()
    mfa_secret = pyotp.random_base32()

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        cur.close()
        return False, "Account already exists.", None

    try:
        cur.execute("""
            INSERT INTO users (email, fullname, dob, phone, address, salt, hashed_passphrase, role, mfa_secret, recovery_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (email, name, dob, phone, address, salt, hashed, 'user', mfa_secret, recovery_code))
        mysql.connection.commit()
        log_user_action(email, "Register", "Success")
        return True, f"Registration successful!", recovery_code
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error during registration: {e}")  # Log the error for debugging
        log_user_action(email, "Register", "Fail")
        return False, "An error occurred during registration.", None
    finally:
        cur.close()


def process_login(email, passphrase):
    email = sanitize_input(email)
    passphrase = sanitize_input(passphrase)

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()

    now = datetime.now()
    if not user:
        log_user_action(email, "Login failed - No such user", "Failed")
        return {"success": False, "message": "Wrong email or password"}

    # Đếm sai trong 2 phút
    if user['last_failed_login']:
        time_diff = now - user['last_failed_login']
        if time_diff > timedelta(minutes=2):
            cur.execute(
                "UPDATE users SET failed_attempts = 0 WHERE email = %s", (email,))
            mysql.connection.commit()
            user['failed_attempts'] = 0

    if user['is_locked']:
        delta = now - user['last_failed_login']
        if delta < timedelta(minutes=5):
            return {"success": False, "locked": True}
        else:
            cur.execute(
                "UPDATE users SET is_locked = FALSE, failed_attempts = 0 WHERE email = %s", (email,))
            mysql.connection.commit()

    # Kiểm tra mật khẩu
    hashed = hash_with_salt(passphrase, user['salt'])
    if hashed != user['hashed_passphrase']:
        failed = user['failed_attempts'] + 1
        is_locked = failed >= 5
        cur.execute("""
            UPDATE users 
            SET failed_attempts = %s, last_failed_login = %s, is_locked = %s 
            WHERE email = %s
        """, (failed, now, is_locked, email))
        mysql.connection.commit()
        log_user_action(email, "Login failed - wrong pass", "Failed")
        return {"success": False, "message": "Wrong email or password"}

    # Đúng pass → reset
    cur.execute("""
        UPDATE users SET failed_attempts = 0, last_failed_login = NULL WHERE email = %s
    """, (email,))
    mysql.connection.commit()
    log_user_action(email, "Login success", "Pending MFA")

    return {"success": True}
