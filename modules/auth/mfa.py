# modules/auth/mfa.py
from datetime import datetime, timedelta
import random
import pyotp
import qrcode
import io
import base64
from flaskapi.extensions import mysql
from modules.utils.mail import send_email  # giả định bạn có hàm này

# Gửi OTP và lưu vào DB


def generate_and_send_otp(email):
    otp = f"{random.randint(100000, 999999)}"
    created = datetime.now()
    expires = created + timedelta(minutes=5)

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO otp_codes (email, otp_code, created_at, expires_at)
        VALUES (%s, %s, %s, %s)
    """, (email, otp, created, expires))
    mysql.connection.commit()

    # Gửi mail
    send_email(email, otp)

    return otp

# Kiểm tra OTP trong DB


def verify_otp_code(email, input_code):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT otp_code, expires_at FROM otp_codes
        WHERE email = %s ORDER BY created_at DESC LIMIT 1
    """, (email,))
    record = cur.fetchone()
    if not record:
        return False
    if datetime.now() > record['expires_at']:
        return False
    return input_code == record['otp_code']

# TOTP: Sinh secret nếu chưa có


def get_or_create_mfa_secret(email):
    cur = mysql.connection.cursor()
    cur.execute("SELECT mfa_secret FROM users WHERE email = %s", (email,))
    result = cur.fetchone()

    if result and result['mfa_secret']:
        return result['mfa_secret']
    else:
        secret = pyotp.random_base32()
        cur.execute(
            "UPDATE users SET mfa_secret = %s WHERE email = %s", (secret, email))
        mysql.connection.commit()
        return secret

# Sinh mã QR base64 từ secret


def generate_qr_code(email):
    secret = get_or_create_mfa_secret(email)
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=email, issuer_name="Secure Vault")
    qr = qrcode.make(uri)
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')
    qr_code = base64.b64encode(buffer.getvalue()).decode()
    return qr_code

# Xác minh mã từ Google Authenticator


def verify_totp_code(email, input_code):
    secret = get_or_create_mfa_secret(email)
    totp = pyotp.TOTP(secret)
    return totp.verify(input_code)


def expire_otp_code(email):
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE otp_codes SET expires_at = %s
        WHERE email = %s AND expires_at > %s
    """, (datetime.now(), email, datetime.now()))
    mysql.connection.commit()
