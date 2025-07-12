# file: modules/keys/recovery_utils.py (ví dụ)

import os
import base64
import json
from pathlib import Path

# ... các import và hàm tiện ích khác ...
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .key_extensions import get_user_dir, read_json_file, write_json_file
from cryptography.hazmat.primitives import serialization
import hashlib
# --- HÀM 1: MÃ HÓA RECOVERY CODE (LƯU VÀO Recovery_info.json) ---

def encrypt_recovery_code(
    email: str,
    recovery_code: str, 
    passphrase: str, 
    salt: bytes
) -> tuple[bool, str]:
    """
    Mã hóa recovery code và lưu vào file 'Recovery_info.json'.
    """
    try:
        # Suy diễn khóa AES từ passphrase và salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000,
        )
        aes_key = kdf.derive(passphrase.encode('utf-8'))

        # Mã hóa recovery code
        nonce = os.urandom(12)
        aesgcm = AESGCM(aes_key)
        encrypted_data = aesgcm.encrypt(nonce, recovery_code.encode('utf-8'), None)
        encrypted_recovery_key_b64 = base64.b64encode(nonce + encrypted_data).decode('utf-8')

        # Tạo dictionary để lưu
        data_to_save = {
            "Encrypt_recovery_key": encrypted_recovery_key_b64
        }
        
        # --- THAY ĐỔI TÊN FILE OUTPUT ---
        user_dir = get_user_dir(email)
        output_path = user_dir / "Recovery_info.json" # <-- Tên file và định dạng mới
        # -------------------------------
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2)
            
        return True, f"Thông tin khôi phục đã được mã hóa và lưu thành công tại {output_path}"

    except Exception as e:
        return False, f"Lỗi khi mã hóa thông tin khôi phục: {e}"


# --- HÀM 2: GIẢI MÃ RECOVERY CODE (ĐỌC TỪ Recovery_info.json) ---

def decrypt_recovery_code(
    email: str,
    passphrase: str,
    salt: bytes
) -> tuple[bool, str]:
    """
    Đọc file 'Recovery_info.json', giải mã và trả về recovery code.
    """
    try:
        # --- THAY ĐỔI TÊN FILE INPUT ---
        user_dir = get_user_dir(email)
        input_path = user_dir / "Recovery_info.json" # <-- Tên file và định dạng mới
        # -----------------------------

        if not input_path.exists():
            return False, "Không tìm thấy file thông tin khôi phục (Recovery_info.json)."

        with open(input_path, 'r', encoding='utf-8') as f:
            data_from_file = json.load(f)

        # Lấy dữ liệu từ key
        encrypted_recovery_key_b64 = data_from_file.get("Encrypt_recovery_key")
        if not encrypted_recovery_key_b64:
            return False, "Định dạng file không hợp lệ, không tìm thấy key 'Encrypt_recovery_key'."

        # Suy diễn khóa AES
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000,
        )
        aes_key = kdf.derive(passphrase.encode('utf-8'))
        
        # Decode Base64 và giải mã
        encrypted_data_with_nonce = base64.b64decode(encrypted_recovery_key_b64)
        nonce = encrypted_data_with_nonce[:12]
        ciphertext = encrypted_data_with_nonce[12:]
        
        aesgcm = AESGCM(aes_key)
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        
        recovery_code = decrypted_bytes.decode('utf-8')
        
        return True, recovery_code

    except FileNotFoundError:
        return False, "Không tìm thấy file thông tin khôi phục."
    except json.JSONDecodeError:
        return False, "File thông tin khôi phục bị hỏng, không phải là định dạng JSON hợp lệ."
    except Exception as e:
        return False, f"Giải mã thất bại. Sai mật khẩu hoặc file bị hỏng. ({e})"
    
def encrypt_private_key_by_recovery_code(
    email: str,
    private_key_obj, # Nhận vào đối tượng private key đã giải mã
    passphrase: str,
    salt: bytes
) -> tuple[bool, str]:
    """
    Sử dụng passphrase để giải mã recovery_code, sau đó dùng chính
    recovery_code đó làm "khóa" để mã hóa lại private_key và lưu vào
    file Recovery_info.json.

    Args:
        email (str): Email của người dùng.
        private_key_obj: Đối tượng RSAPrivateKey đã được giải mã.
        passphrase (str): Mật khẩu hiện tại của người dùng.
        salt (bytes): Salt của người dùng (lấy từ CSDL).

    Returns:
        Một tuple (success: bool, message: str).
    """
    try:
        # --- BƯỚC 1: GIẢI MÃ RECOVERY CODE BẰNG PASSPHRASE ---
        success, recovery_code = decrypt_recovery_code(email, passphrase, salt)
        if not success:
            # Nếu giải mã thất bại, recovery_code sẽ là thông báo lỗi
            return False, f"Không thể lấy mã khôi phục: {recovery_code}"
        
        print("Đã lấy thành công mã khôi phục.")

        # --- BƯỚC 2: DÙNG RECOVERY CODE LÀM KHÓA AES MỚI ---
        # Chúng ta sẽ băm recovery_code bằng SHA-256 để tạo ra một khóa AES-256 an toàn
        # Đây là một lớp bảo vệ bổ sung thay vì dùng recovery_code trực tiếp.
        recovery_code_aes_key = hashlib.sha256(recovery_code.encode('utf-8')).digest()

        # --- BƯỚC 3: MÃ HÓA PRIVATE KEY BẰNG KHÓA MỚI NÀY ---
        # Chuyển đối tượng private key thành dạng bytes PEM
        private_pem_bytes = private_key_obj.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Mã hóa PEM bytes bằng khóa AES suy diễn từ recovery code
        nonce = os.urandom(12)
        aesgcm = AESGCM(recovery_code_aes_key)
        encrypted_private_key = aesgcm.encrypt(nonce, private_pem_bytes, None)

        # Encode kết quả thành Base64
        encrypted_private_key_b64 = base64.b64encode(nonce + encrypted_private_key).decode('utf-8')

        # --- BƯỚC 4: LƯU VÀO FILE Recovery_info.json ---
        user_dir = get_user_dir(email)
        info_path = user_dir / "Recovery_info.json"
        
        # Đọc nội dung file hiện có (nếu có) để không ghi đè mất các key khác
        recovery_data = read_json_file(info_path)
        
        # Thêm hoặc cập nhật key mới
        recovery_data["Encrypt_private_key_by_recovery"] = encrypted_private_key_b64
        
        # Ghi lại toàn bộ dictionary vào file
        write_json_file(info_path, recovery_data)
        
        return True, "Đã mã hóa thành công private key bằng mã khôi phục."

    except Exception as e:
        return False, f"Lỗi khi mã hóa private key bằng mã khôi phục: {e}"


# --- HÀM 2: GIẢI MÃ PRIVATE KEY BẰNG RECOVERY CODE ---

def decrypt_private_key_by_recovery_code(
    email: str,
    passphrase: str,
    salt: bytes
):
    """
    Giải mã recovery_code bằng passphrase, sau đó dùng recovery_code
    để giải mã private key và trả về đối tượng private key.

    Args:
        email (str): Email của người dùng.
        passphrase (str): Mật khẩu hiện tại của người dùng.
        salt (bytes): Salt của người dùng.

    Returns:
        Đối tượng RSAPrivateKey nếu thành công, None nếu thất bại.
    """
    try:
        # --- BƯỚC 1: GIẢI MÃ RECOVERY CODE BẰNG PASSPHRASE ---
        success, recovery_code = decrypt_recovery_code(email, passphrase, salt)
        if not success:
            print(f"Lỗi khi giải mã recovery code: {recovery_code}")
            return None

        # --- BƯỚC 2: ĐỌC DỮ LIỆU PRIVATE KEY ĐÃ MÃ HÓA ---
        user_dir = get_user_dir(email)
        info_path = user_dir / "Recovery_info.json"
        recovery_data = read_json_file(info_path)
        
        encrypted_private_key_b64 = recovery_data.get("Encrypt_private_key_by_recovery")
        if not encrypted_private_key_b64:
            print("Không tìm thấy private key được mã hóa bằng mã khôi phục.")
            return None

        # --- BƯỚC 3: DÙNG RECOVERY CODE ĐỂ TẠO KHÓA AES VÀ GIẢI MÃ ---
        # Băm recovery code để lấy lại đúng khóa AES đã dùng để mã hóa
        recovery_code_aes_key = hashlib.sha256(recovery_code.encode('utf-8')).digest()

        # Decode Base64 và tách nonce
        encrypted_data_with_nonce = base64.b64decode(encrypted_private_key_b64)
        nonce = encrypted_data_with_nonce[:12]
        ciphertext = encrypted_data_with_nonce[12:]
        
        # Giải mã private key PEM
        aesgcm = AESGCM(recovery_code_aes_key)
        decrypted_private_key_pem_bytes = aesgcm.decrypt(nonce, ciphertext, None)

        # --- BƯỚC 4: TẢI PRIVATE KEY TỪ PEM VÀ TRẢ VỀ ---
        private_key_obj = serialization.load_pem_private_key(
            decrypted_private_key_pem_bytes,
            password=None
        )
        
        print("Giải mã thành công private key bằng mã khôi phục.")
        return private_key_obj

    except Exception as e:
        print(f"Lỗi khi giải mã private key bằng mã khôi phục: {e}")
        return None