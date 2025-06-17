from flaskapi.app import mysql
from modules.auth.validator import (
    is_valid_email, is_valid_date, is_valid_phone,
    is_strong_passphrase, sanitize_input
)


def register_user(data: dict) -> tuple:
    email = sanitize_input(data.get("email", ""))
    name = sanitize_input(data.get("name", ""))
    dob = sanitize_input(data.get("dob", ""))
    phone = sanitize_input(data.get("phone", ""))
    address = sanitize_input(data.get("address", ""))
    pass1 = data.get("passphrase", "")
    pass2 = data.get("repeat_passphrase", "")

    if not all([email, name, dob, phone, address, pass1, pass2]):
        return False, "All fields are required."
    if not is_valid_email(email):
        return False, "Invalid email format."
    if not is_valid_date(dob):
        return False, "Invalid date format."
    if not is_valid_phone(phone):
        return False, "Phone must be 10 digits."
    if not is_strong_passphrase(pass1):
        return False, "Passphrase too weak (min 8 chars, upper, digit, symbol)."
    if pass1 != pass2:
        return False, "Passphrases do not match."

    from hashlib import sha256
    hashed = sha256(pass1.encode()).hexdigest()

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        cur.close()
        return False, "Account already exists."

    cur.execute(
        "INSERT INTO users (email, name, dob, phone, address, passphrase) VALUES (%s, %s, %s, %s, %s, %s)",
        (email, name, dob, phone, address, hashed)
    )
    mysql.connection.commit()
    cur.close()
    return True, "Registration successful."
