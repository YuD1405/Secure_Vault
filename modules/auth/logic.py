from flaskapi.extensions import mysql
from modules.auth.validator import (
    is_valid_email, is_valid_date, is_valid_phone,
    is_strong_passphrase, sanitize_input
)
import os
import random
import string
import hashlib
import pyotp
import secrets
import base64
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timedelta
from modules.crypto.key_generator import derive_aes_key, create_new_key
from modules.crypto.recovery_code import encrypt_recovery_code, decrypt_recovery_code, encrypt_private_key_by_recovery_code, decrypt_private_key_by_recovery_code
from modules.crypto.key_extensions import save_temp_private_key, write_temp_recovery_code, read_temp_recovery_code

def generate_salt(length=16):
    return os.urandom(length).hex()

def hash_with_salt(passphrase, salt):
    return hashlib.sha256((passphrase + salt).encode()).hexdigest()

def generate_recovery_code(length_bytes=16):
    return secrets.token_urlsafe(length_bytes)

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
        print("Error while querying salt:", e)
        return None

def get_encrypted_recovery_code_from_db(email: str) -> str:
    cur = mysql.connection.cursor()
    cur.execute("SELECT encrypted_recovery_code FROM users WHERE email = %s", (email,))
    row = cur.fetchone()
    cur.close()

    if not row or not row['encrypted_recovery_code']:
        raise ValueError("Recovery code not found or empty.")
    
    return row['encrypted_recovery_code']

from modules.crypto.key_management import get_active_private_key
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
    success_1, message_1, encrypted_recovery_code = encrypt_recovery_code(recovery_code, pass1, salt)
    
    if not success_1:
        return False, message_1, None
    
    mfa_secret = pyotp.random_base32()

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        cur.close()
        return False, "Account already exists.", None

    try:
        cur.execute("""
            INSERT INTO users (email, fullname, dob, phone, address, salt, hashed_passphrase, role, mfa_secret, encrypted_recovery_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (email, name, dob, phone, address, salt, hashed, 'user', mfa_secret, encrypted_recovery_code))
        mysql.connection.commit()
        
        # tạo khóa RSA và lưu 2 bản : 1 mã hóa bằng pw, 1 mã hóa bằng recovery key
        aes_key = derive_aes_key(pass1, salt)
        success = create_new_key(email, aes_key)
        if success:
            private_key_pem = get_active_private_key(email, aes_key)
            success_pri, msg_pri = encrypt_private_key_by_recovery_code(email, private_key_pem, recovery_code, salt)
        
            if not success_pri:
                print(f"[Register] Lỗi khi xử lí giải mã và mã hóa bằng recovery key: {msg_pri}")
                
        else:
            return False, "An error occurred during registration - generating new RSA keys.", None
    
        return True, f"Registration successful!", recovery_code
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error during registration: {e}")  # Log the error for debugging
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
        return {"success": False, "message": "Wrong email or password"}

    # Đúng pass → reset
    cur.execute("""
        UPDATE users SET failed_attempts = 0, last_failed_login = NULL WHERE email = %s
    """, (email,))
    mysql.connection.commit()

    # aes_key = derive_aes_key(passphrase, user['salt'])
    # check_and_manage_own_keys(email, aes_key, passphrase)
    
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
            return False, "Please fill in all required fields."

        if not is_valid_email(email):
            return False, "Invalid email format."

        if not is_valid_date(dob):
            return False, "Invalid date of birth format (expected yyyy-mm-dd)."

        if not is_valid_phone(phone):
            return False, "Phone number must be exactly 10 digits."

        # --- Truy vấn dữ liệu hiện tại ---
        cur.execute("SELECT fullname, phone, address, dob, hashed_passphrase, salt FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        if not row:
            return False, "User account not found."

        no_info_change = (
            row["fullname"] == full_name and
            row["phone"] == phone and
            row["address"] == address and
            row["dob"].strftime("%Y-%m-%d") == dob
        )

        # Nếu không có thay đổi gì
        if no_info_change and not (pass1 or pass2):
            return False, "No changes were made."

        # --- Cập nhật thông tin cá nhân nếu có thay đổi ---
        if not no_info_change:
            cur.execute("""
                UPDATE users SET fullname = %s, phone = %s, address = %s, dob = %s
                WHERE email = %s
            """, (full_name, phone, address, dob, email))

        # --- Nếu có ý định đổi passphrase ---
        if pass1 or pass2:
            if not (pass1 and pass2):
                return False, "Please enter both your current and new passphrase to change your password."

            if pass1 == pass2:
                return False, "The new passphrase must be different from the current one."

            if not is_strong_passphrase(pass2):
                return False,  "New passphrase is too weak. It must contain at least 8 characters, an uppercase letter, a number, and a special symbol."

            # Kiểm tra passphrase cũ đúng không
            cur.execute("SELECT hashed_passphrase, salt FROM users WHERE email = %s", (email,))
            row = cur.fetchone()

            if not row:
                return False, "User account not found."

            stored_hash = row["hashed_passphrase"]
            stored_salt = row["salt"]
            input_hash = hash_with_salt(pass1, stored_salt)

            if input_hash != stored_hash:
                return False, "Current passphrase is incorrect."

            # Xử lí giải mã recovery code bằng pw cũ và mã hóa lại bằng pw mới
            try:
                encrypted_recovery_code = get_encrypted_recovery_code_from_db(email)
                success, recovery_code = decrypt_recovery_code(encrypted_recovery_code, pass1, stored_salt)
                if success:
                    success_1, message_1, new_encrypted_recovery_code = encrypt_recovery_code(recovery_code, pass2, stored_salt)
    
                if not success_1:
                    return False, message_1
                
            except Exception as e:
                print(f"[recovery] Lỗi khi xử lí giải mã recovery code bằng pw cũ và mã hóa lại bằng pw mới: {e}")
                return False, f"[recovery] Lỗi khi xử lí giải mã recovery code bằng pw cũ và mã hóa lại bằng pw mới: {e}"
            
            # Hash passphrase mới
            new_hash = hash_with_salt(pass2, stored_salt)
            # cur.execute("""
            #     UPDATE users SET hashed_passphrase = %s WHERE email = %s
            # """, (new_hash, email))
            cur.execute("""
                UPDATE users SET hashed_passphrase = %s, encrypted_recovery_code = %s
                WHERE email = %s
            """, (new_hash, new_encrypted_recovery_code, email))

        # Commit tất cả cập nhật (dù chỉ là thông tin cá nhân)
        mysql.connection.commit()
        cur.close()
        return True, "Information has been successfully updated."

    except Exception as e:
        return False, "An error occurred while updating the information."
    
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
    try:
        salt = get_salt_from_db(email)

        private_key_obj = decrypt_private_key_by_recovery_code(email, recovery_code_input, salt)
        if not private_key_obj:
            return False, "Invalid recovery code or corrupted key file."
        
        private_key_pem = private_key_obj.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
        )
        
        save_temp_private_key(email, private_key_pem)
        write_temp_recovery_code(email, recovery_code_input)
        return True, None

    except Exception as e:
        return False, f"Error verifying recovery: {e}"
    
def reset_password_and_update_recovery_code_in_db(email, new_password):
    try:
        if not is_strong_passphrase(new_password):
            return False,  "New passphrase is too weak. It must contain at least 8 characters, an uppercase letter, a number, and a special symbol."
        recovery_code = read_temp_recovery_code(email)
        
        cursor = mysql.connection.cursor()

        # Tạo salt ngẫu nhiên
        salt = get_salt_from_db(email)
        hashed_pass = hash_with_salt(new_password, salt)

        # Mã hóa lại recovery_code bằng passphrase mới
        success_enc, msg_enc, encrypted_recovery = encrypt_recovery_code(recovery_code, new_password, salt)
        if not success_enc:
            return False, f"Failed to encrypt recovery code: {msg_enc}"
        
        # Cập nhật mật khẩu mới + xóa recovery_code
        query = """
            UPDATE users 
            SET hashed_passphrase = %s, salt = %s, encrypted_recovery_code = %s
            WHERE email = %s
        """
        cursor.execute(query, (hashed_pass, salt, encrypted_recovery, email))
        mysql.connection.commit()
        cursor.close()

        return True, None
    except Exception as e:
        print("Password reset error:", e)
        return False, "Database error"
    
