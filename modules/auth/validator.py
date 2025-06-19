import re
from datetime import datetime


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))


def is_valid_phone(phone: str) -> bool:
    return bool(re.match(r"^\d{10}$", phone))


def is_valid_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def is_strong_passphrase(passphrase: str) -> bool:
    if len(passphrase) < 8:
        return False
    if not re.search(r"[A-Z]", passphrase):
        return False
    if not re.search(r"\d", passphrase):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", passphrase):
        return False
    return True


def sanitize_input(s: str) -> str:
    return re.sub(r"[<>\"'%;()&+]", "", s).strip()