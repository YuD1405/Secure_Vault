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
        if user['last_failed_login'] is None:
            return {"success": False, "locked_by_admin": True}
        
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

    return {"success": True, "role": user['role']}

def get_user_by_email(email):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, email, fullname, dob, phone, address 
        FROM users 
        WHERE email = %s
    """, (email,))
    
    row = cur.fetchone()
    cur.close()

    if row:

        return {
            "id": row["id"],
            "email": row["email"],
            "fullname": row["fullname"],
            "dob": row["dob"].strftime("%Y-%m-%d") if row["dob"] else "",
            "phone": row["phone"],
            "address": row["address"]
        }
    return None

def update_user_info_in_db(email: str, full_name: str, phone: str, address: str, dob: str, pass1: str, pass2: str) -> tuple[bool, str]:
    try:
        cur = mysql.connection.cursor()

        # --- Kiểm tra bắt buộc ---
        if not all([email, full_name, dob, phone, address]):
            return False, "Vui lòng điền đầy đủ thông tin."

        if not is_valid_email(email):
            return False, "Email không hợp lệ."

        if not is_valid_date(dob):
            return False, "Ngày sinh không đúng định dạng (yyyy-mm-dd)."

        if not is_valid_phone(phone):
            return False, "Số điện thoại phải có đúng 10 chữ số."

        # --- Cập nhật thông tin cá nhân ---
        cur.execute("""
            UPDATE users
            SET fullname = %s, phone = %s, address = %s, dob = %s
            WHERE email = %s
        """, (full_name, phone, address, dob, email))

        # --- Nếu có yêu cầu đổi passphrase ---
        if pass1 and pass2:
            if pass1 == pass2:
                return False, "Passphrase mới phải khác passphrase cũ."

            if not is_strong_passphrase(pass2):
                return False, "Passphrase mới quá yếu. Cần ≥8 ký tự, chữ hoa, số, ký hiệu."
            
            # Lấy passphrase hash cũ từ DB
            cur.execute("SELECT hashed_passphrase, salt FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            
            if not row:
                return False, "Không tìm thấy tài khoản người dùng."

            stored_hash = row["hashed_passphrase"]
            stored_salt = row["salt"]
            
            input_hash = hash_with_salt(pass1, stored_salt)
            print(input_hash)
            print(stored_hash)
            print(stored_salt)
            if input_hash != stored_hash:
                return False, "Passphrase hiện tại không đúng."
            
            # Hash passphrase mới
            new_hash = hash_with_salt(pass2, stored_salt)

            cur.execute("""
                UPDATE users SET hashed_passphrase = %s WHERE email = %s
            """, (new_hash, email))
        else:
            return False, "Please enter both passphrase input for changing passphrase"
        
        mysql.connection.commit()
        cur.close()
        return True, "Thông tin đã được cập nhật thành công."

    except Exception as e:
        return False, "Đã xảy ra lỗi khi cập nhật thông tin."
    
def check_correct_pw(email: str, passphrase:str):
    email = sanitize_input(email)
    passphrase = sanitize_input(passphrase)

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    
    hashed = hash_with_salt(passphrase, user['salt'])
    if hashed != user['hashed_passphrase']:
        return False
    return True

def verify_recovery_code_from_db(email, recovery_code_input):
    cursor = mysql.connection.cursor()

    query = "SELECT recovery_code FROM users WHERE email = %s"
    cursor.execute(query, (email,))
    result = cursor.fetchone()
    cursor.close()

    if not result:
        return False, "User not found"

    db_recovery_code = result["recovery_code"]

    if recovery_code_input == db_recovery_code:
        return True, None
    else:
        return False, "Invalid recovery code"
    
def reset_password_in_db(email, new_password):
    try:
        cursor = mysql.connection.cursor()

        # Tạo salt ngẫu nhiên
        salt = os.urandom(16).hex()
        hash_input = new_password + salt
        hashed_pass = hashlib.sha256(hash_input.encode()).hexdigest()

        # Cập nhật mật khẩu mới + xóa recovery_code
        query = """
            UPDATE users 
            SET hashed_passphrase = %s, salt = %s, recovery_code = NULL 
            WHERE email = %s
        """
        cursor.execute(query, (hashed_pass, salt, email))
        mysql.connection.commit()
        cursor.close()

        return True, None
    except Exception as e:
        print("Password reset error:", e)
        return False, "Database error"
    
def get_salt_from_db(email: str) -> bytes:
    """
    Lấy salt từ bảng `rsa_keys` trong MySQL thông qua email.
    Trả về salt dạng bytes hoặc None nếu không tìm thấy.
    """
    try:
        cur = mysql.connection.cursor()
        query = "SELECT salt FROM users WHERE email = %s"
        cur.execute(query, (email,))
        result = cur.fetchone()
        cur.close()
        if result:
            return result["salt"]
        return None
    except Exception as e:
        print("Lỗi khi truy vấn salt:", e)
        return None
