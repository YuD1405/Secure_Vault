from datetime import datetime, timedelta
import random
from flaskapi.extensions import mysql


def generate_otp(email):
    code = f"{random.randint(100000, 999999)}"
    created = datetime.now()
    expires = created + timedelta(minutes=5)

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO otp_codes (email, otp_code, created_at, expires_at) VALUES (%s, %s, %s, %s)",
                   (email, code, created, expires))
    mysql.connection.commit()
    return code


def validate_otp(email, input_code):
    cur = mysql.connection.cursor
    cur.execute("""
        SELECT * FROM otp_codes WHERE email = %s ORDER BY created_at DESC LIMIT 1
    """, (email,))
    record = cur.fetchone()
    if not record:
        return False
    if datetime.now() > record['expires_at']:
        return False
    return input_code == record['otp_code']
