import base64
from datetime import datetime, timedelta
from typing import List, Tuple
import os
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from modules.crypto.key_extensions import get_user_dir, get_latest_key_path, read_json_file, get_key_files, hashlib, write_json_file, read_temp_private_key
from modules.crypto.key_generator import get_latest_key_path, create_new_key, derive_aes_key
from modules.auth.logic import get_encrypted_recovery_code_from_db, get_salt_from_db
from modules.crypto.recovery_code import encrypt_private_key_by_recovery_code, decrypt_recovery_code

# Kiểm tra tình trạng cặp khóa RSA
def check_and_manage_own_keys(email: str, passphrase, aes_key: bytes, salt):
    """Kiểm tra trạng thái khoá của người dùng và tạo mới nếu cần."""
    print(f"\n--- [QUẢN LÝ KHOÁ CHO {email}] ---")
    user_dir = get_user_dir(email)
    latest_key_path = get_latest_key_path(user_dir)

    if not latest_key_path:
        print("Phát hiện người dùng chưa có khoá nào. Đang tạo khoá đầu tiên...")
        create_new_key(email, aes_key)
        return

    key_data = read_json_file(latest_key_path)
    expiry_date_str = key_data.get("public_info", {}).get("expiry_date")
    
    if not expiry_date_str or datetime.now() > datetime.fromisoformat(expiry_date_str):
        print("Khoá hiện tại đã hết hạn hoặc không hợp lệ. Bắt buộc phải tạo khoá mới...")
        # create_new_key(email, aes_key)
        regenerate_key_handling(email, passphrase, aes_key, salt)
    else:
        print(f"Khoá đang hoạt động và còn hạn đến {datetime.fromisoformat(expiry_date_str).strftime('%Y-%m-%d')}.")

# Lấy khóa private mới nhất / active (đã giải mã)
def get_active_private_key(email: str, aes_key: bytes) -> rsa.RSAPrivateKey | None:
    """Giải mã và trả về đối tượng private key đang hoạt động."""
    user_dir = get_user_dir(email)
    latest_key_path = get_latest_key_path(user_dir)
    if not latest_key_path: return None

    key_data = read_json_file(latest_key_path)
    if key_data.get('status') != 'active': return None

    encrypted_b64 = key_data["private_info"]["encrypted_private_key_b64"]
    encrypted_data = base64.b64decode(encrypted_b64)
    nonce, ciphertext = encrypted_data[:12], encrypted_data[12:]
    
    decrypted_pem = AESGCM(aes_key).decrypt(nonce, ciphertext, None)
    
    print("Đã giải mã thành công khoá riêng tư đang hoạt động.")
    return serialization.load_pem_private_key(decrypted_pem, password=None)

# Lấy khóa public mới nhất / active
def get_active_public_info(email: str) -> dict | None:
    """Lấy thông tin công khai của cặp khoá đang hoạt động."""
    user_dir = get_user_dir(email)
    latest_key_path = get_latest_key_path(user_dir)
    if not latest_key_path: return None
    
    key_data = read_json_file(latest_key_path)
    return key_data.get('public_info') if key_data.get('status') == 'active' else None

# Lấy toàn bộ khóa pri và pub của user
def trim_public_key(pem_str: str) -> str:
    """
    Xoá phần BEGIN/END và nối chuỗi public key PEM thành 1 dòng base64.
    """
    lines = pem_str.strip().splitlines()
    # Bỏ BEGIN/END dòng đầu/cuối
    core_lines = [line for line in lines if "-----" not in line]
    return ''.join(core_lines)

def get_all_key_strings(email: str) -> List[dict]:
    """
    Trả về danh sách tất cả các key của người dùng gồm:
    - chuỗi private key đã mã hóa (base64)
    - chuỗi public key PEM
    - ngày hết hạn
    - trạng thái (active/deactivated)
    
    Returns:
        List[dict]: danh sách mỗi dict chứa thông tin của 1 file key
    """
    user_dir = get_user_dir(email)
    key_files = get_key_files(user_dir)

    all_keys = []

    for key_path in key_files:
        try:
            key_data = read_json_file(key_path)

            encrypted_private_key = key_data["private_info"]["encrypted_private_key_b64"]
            public_key = key_data["public_info"]["public_key_pem"]
            public_key_trimmed = trim_public_key(public_key)
            expiry = key_data["public_info"]["expiry_date"]
            status = key_data.get("status", "unknown")

            all_keys.append({
                "file": key_path.name,
                "private_key_b64": encrypted_private_key,
                "public_key_pem": public_key_trimmed,
                "expiry_date": expiry,
                "status": status
            })
        except Exception as e:
            print(f"[!] Lỗi khi đọc {key_path.name}: {e}")
            continue

    return all_keys

# Regenerate keys
def regenerate_key_handling(email: str, passphrase, aes_key, salt) -> bool:
    """
    Tạo mới cặp khóa RSA, mã hóa private key bằng cả passphrase và recovery code.
    """
    # Tạo cặp khóa mới
    success = create_new_key(email, aes_key)
    if success:
        private_key_pem = get_active_private_key(email, aes_key)
    else:
        return False
        
    # Giải mã recovery code → mã hóa lại private key
    try:
        encrypted_recovery_code = get_encrypted_recovery_code_from_db(email)
        recovery_code = decrypt_recovery_code(encrypted_recovery_code, passphrase, salt)
        success_pri, msg_pri = encrypt_private_key_by_recovery_code(email, private_key_pem, recovery_code, salt)
        
        if not success_pri:
            print(f"[recovery] Lỗi khi xử lí giải mã và mã hóa bằng recovery key: {msg_pri}")
            
    except Exception as e:
        print(f"[recovery] Lỗi khi xử lí giải mã và mã hóa bằng recovery key: {e}")
        return False

    print(recovery_code)
    return True

# Giari mã pri bằng pw cũ sau đó mã lại bằng pw mới và lưu vào json
def re_encrypt_private_key_with_new_passphrase(
    email: str, 
    old_passphrase: str, 
    new_passphrase: str
) -> tuple[bool, str]:
    """
    Giải mã private key đang hoạt động bằng passphrase cũ, sau đó mã hoá lại
    bằng passphrase mới và cập nhật file key.

    Đây là chức năng cốt lõi cho việc "Đổi mật khẩu".

    Args:
        email (str): Email của người dùng đang thực hiện đổi mật khẩu.
        old_passphrase (str): Passphrase hiện tại (cũ) của người dùng.
        new_passphrase (str): Passphrase mới người dùng muốn đặt.

    Returns:
        Một tuple (success: bool, message: str).
    """
    print(f"\n--- [BẮT ĐẦU QUÁ TRÌNH TÁI MÃ HOÁ PRIVATE KEY CHO {email}] ---")
    try:
        # --- BƯỚC 1: LẤY THÔNG TIN VÀ KHÓA CŨ ---
        user_dir = get_user_dir(email)
        latest_key_path = get_latest_key_path(user_dir)

        if not latest_key_path:
            return False, "No key found to proceed. Please create a key first."

        key_data = read_json_file(latest_key_path)
        if key_data.get('status') != 'active':
            return False, "The latest key is not in active status."
            
        # Suy diễn khoá AES từ passphrase CŨ
        try:
            salt = get_salt_from_db(email)
            old_aes_key = derive_aes_key(old_passphrase, salt)
        except Exception as e:
            return False, f"Error generating AES key: {e}"
    
        # --- BƯỚC 2: GIẢI MÃ PRIVATE KEY BẰNG KHÓA CŨ ---
        encrypted_b64 = key_data["private_info"]["encrypted_private_key_b64"]
        encrypted_data = base64.b64decode(encrypted_b64)
        
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        
        try:
            aesgcm_old = AESGCM(old_aes_key)
            decrypted_private_key_pem_bytes = aesgcm_old.decrypt(nonce, ciphertext, None)
            print("Giải mã thành công private key bằng passphrase cũ.")
        except Exception: # Thường là InvalidTag
            return False, "Old password is incorrect."

        # --- BƯỚC 3: MÃ HOÁ LẠI PRIVATE KEY BẰNG KHÓA MỚI ---
        # Suy diễn khoá AES từ passphrase MỚI
        try:
            new_aes_key = derive_aes_key(new_passphrase, salt)
        except Exception as e:
            return False, f"Error generating AES key: {e}"  
        
        # Dùng khoá AES mới để mã hoá lại private key PEM đã giải mã ở trên
        new_nonce = os.urandom(12)
        aesgcm_new = AESGCM(new_aes_key)
        re_encrypted_private_key = aesgcm_new.encrypt(new_nonce, decrypted_private_key_pem_bytes, None)
        
        # Encode lại thành Base64
        re_encrypted_private_key_b64 = base64.b64encode(new_nonce + re_encrypted_private_key).decode('utf-8')
        print("Mã hoá lại thành công private key bằng passphrase mới.")

        # --- BƯỚC 4: CẬP NHẬT FILE KEY VỚI PRIVATE KEY ĐÃ MÃ HOÁ LẠI ---
        key_data["private_info"]["encrypted_private_key_b64"] = re_encrypted_private_key_b64
        
        # Ghi đè lại file key cũ với dữ liệu đã cập nhật
        write_json_file(latest_key_path, key_data)
        
        print(f"Đã cập nhật thành công file {latest_key_path.name}.")
        return True, "Password changed and keys re-encrypted successfully!"

    except Exception as e:
        print(f"Lỗi nghiêm trọng trong quá trình tái mã hoá: {e}")
        return False, f"An unknown error occurred: {e}"
    
def reencrypt_private_key_after_recovery(email, new_pass):
    """
    Dùng trong quá trình khôi phục tài khoản: 
    - Đọc file private key tạm đã giải mã trước đó bằng recovery code
    - Mã hóa lại bằng passphrase mới và lưu vào hệ thống

    Trả về (True, msg) nếu thành công, (False, error) nếu lỗi.
    """
    try:
        # đọc khóa và file tạm
        private_key_pem = read_temp_private_key(email)    
        
        # Derive AES từ passphrase mới
        salt = get_salt_from_db(email)

        # Mã hóa và lưu lại
        user_dir = get_user_dir(email)
        latest_key_path = get_latest_key_path(user_dir)

        if not latest_key_path:
            return False, "No key found to proceed. Please create a key first."

        key_data = read_json_file(latest_key_path)
        if key_data.get('status') != 'active':
            return False, "The latest key is not in active status."
        
        try:
            new_aes_key = derive_aes_key(new_pass, salt)
        except Exception as e:
            return False, f"Error generating AES key: {e}"  
        
        # Dùng khoá AES mới để mã hoá lại private key PEM đã giải mã ở trên
        new_nonce = os.urandom(12)
        aesgcm_new = AESGCM(new_aes_key)
        re_encrypted_private_key = aesgcm_new.encrypt(new_nonce, private_key_pem, None)
        
        # Encode lại thành Base64
        re_encrypted_private_key_b64 = base64.b64encode(new_nonce + re_encrypted_private_key).decode('utf-8')
        print("Mã hoá lại thành công private key bằng passphrase mới.")

        # --- BƯỚC 4: CẬP NHẬT FILE KEY VỚI PRIVATE KEY ĐÃ MÃ HOÁ LẠI ---
        key_data["private_info"]["encrypted_private_key_b64"] = re_encrypted_private_key_b64
        
        # Ghi đè lại file key cũ với dữ liệu đã cập nhật
        write_json_file(latest_key_path, key_data)
        
        print(f"Đã cập nhật thành công file {latest_key_path.name}.")
        return True, "Password changed and keys re-encrypted successfully!"

    except Exception as e:
        print(f"Lỗi nghiêm trọng trong quá trình tái mã hoá: {e}")
        return False, f"An unknown error occurred: {e}"

def extend_key_expiry(email: str, days_to_add: int) -> tuple[bool, str]:
    """
    Extend the expiry date of the user's currently active RSA key.

    Args:
        email (str): The email of the user whose key should be extended.
        days_to_add (int): Number of days to add to the current expiry date.

    Returns:
        A tuple (success: bool, message: str).
    """
    print(f"\n--- [STARTING KEY EXTENSION FOR {email}] ---")

    # Validate input
    if not isinstance(days_to_add, int) or days_to_add <= 0:
        return False, "Number of days must be a positive integer."

    try:
        # 1. Get the latest key path for the user
        user_dir = get_user_dir(email)
        latest_key_path = get_latest_key_path(user_dir)

        if not latest_key_path:
            return False, "No key found to extend."

        # 2. Load key data
        key_data = read_json_file(latest_key_path)

        # 3. Check if key is currently active
        if key_data.get('status') != 'active':
            return False, "Only keys with 'active' status can be extended."

        # 4. Extract and calculate new expiry date
        public_info = key_data.get("public_info")
        if not public_info or "expiry_date" not in public_info:
            return False, "Key data is invalid or missing expiry date."

        current_expiry_str = public_info["expiry_date"]
        current_expiry_date = datetime.fromisoformat(current_expiry_str)
        new_expiry_date = current_expiry_date + timedelta(days=days_to_add)

        print(f"Old expiry date: {current_expiry_date.strftime('%Y-%m-%d')}")
        print(f"New expiry date: {new_expiry_date.strftime('%Y-%m-%d')}")

        # 5. Update expiry date in key data
        key_data["public_info"]["expiry_date"] = new_expiry_date.isoformat()

        # 6. Write updated key data to file
        write_json_file(latest_key_path, key_data)

        return True, f"Key successfully extended. New expiry date: {new_expiry_date.strftime('%Y-%m-%d')}."

    except Exception as e:
        error_message = f"An error occurred while extending the key: {e}"
        print(error_message)
        return False, error_message
