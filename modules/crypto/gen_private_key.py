
import os
import json
import hashlib
import base64
import cv2
from datetime import datetime, timedelta
from pathlib import Path
from pyzbar.pyzbar import decode as qr_decode
 


from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# --- CÁC HẰNG SỐ CẤU HÌNH ---
KEY_DIR = Path("key_manage")
KEY_EXPIRATION_DAYS = 90

# --- CÁC HÀM TIỆN ÍCH CƠ BẢN ---

def get_user_dir(email: str) -> Path:
    """Lấy đường dẫn thư mục của người dùng dựa trên hash email."""
    email_hash = hashlib.sha256(email.encode('utf-8')).hexdigest()
    user_dir = KEY_DIR / email_hash
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir

def derive_aes_key_from_hash(hashed_passphrase_hex: str) -> bytes:
    """Tạo khoá AES 256-bit trực tiếp từ chuỗi hex của hash SHA-256."""
    if len(hashed_passphrase_hex) != 64:
        raise ValueError("Hashed passphrase phải là một chuỗi hex 64 ký tự (SHA-256).")
    return bytes.fromhex(hashed_passphrase_hex)

def get_key_files(user_dir: Path) -> list[Path]:
    """Lấy danh sách các file key của người dùng, sắp xếp theo số thứ tự."""
    files = list(user_dir.glob("key_*.json"))
    files.sort(key=lambda x: int(x.stem.split('_')[1]))
    return files

def get_latest_key_path(user_dir: Path) -> Path | None:
    """Lấy đường dẫn tới file key mới nhất."""
    key_files = get_key_files(user_dir)
    return key_files[-1] if key_files else None

def read_json_file(path: Path) -> dict:
    """Đọc và trả về nội dung của một file JSON."""
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

def write_json_file(path: Path, data: dict):
    """Ghi dữ liệu vào một file JSON."""
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')

# --- CÁC HÀM NGHIỆP VỤ CHÍNH ---

# file: key_utils.py



def add_contact_public_key(user_dir: Path, contact_email: str, public_info: dict):
    """Tiện ích để lưu trữ public_info của một người dùng khác vào danh bạ."""
    contacts_path = user_dir / "contact_public_key.json"
    contacts_data = read_json_file(contacts_path)
    
    contacts_data[contact_email] = public_info
    
    write_json_file(contacts_path, contacts_data)
    print(f"Đã thêm/cập nhật public key của '{contact_email}' vào danh bạ.")

# ... (các import và hàm khác giữ nguyên) ...

def create_new_key(email: str, aes_key: bytes) -> tuple[bool, str]:
    """
    Chủ động tạo một cặp khoá RSA mới và huỷ kích hoạt khoá cũ ngay lập tức.
    Hàm này được dùng cho chức năng "xoay vòng khoá" (Key Rotation).

    Args:
        email (str): Email của người dùng.
        aes_key (bytes): Khoá AES (đã ở dạng bytes) dùng để mã hoá private key mới.

    Returns:
        Một tuple (success: bool, message: str).
    """
    try:
        print(f"\n--- [BẮT ĐẦU XOAY VÒNG KHOÁ CHO {email}] ---")
        user_dir = get_user_dir(email)
        
        # 1. Tìm và huỷ kích hoạt khoá cũ (nếu có)
        latest_key_path = get_latest_key_path(user_dir)
        new_key_number = 1
        if latest_key_path:
            key_data = read_json_file(latest_key_path)
            if key_data.get('status') == 'active':
                key_data['status'] = 'deactivated'
                write_json_file(latest_key_path, key_data)
                print(f"Đã huỷ kích hoạt khoá cũ: {latest_key_path.name}")
            
            latest_key_number = int(latest_key_path.stem.split('_')[1])
            new_key_number = latest_key_number + 1

        # 2. Tạo cặp khoá RSA 2048-bit mới
        private_key_obj = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key_obj = private_key_obj.public_key()
        
        private_pem = private_key_obj.private_bytes(
            encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_pem = public_key_obj.public_bytes(
            encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # 3. Mã hoá private key mới bằng khoá AES đã cung cấp
        nonce = os.urandom(12)

        # --- SỬA LỖI QUAN TRỌNG ---
        # Hàm này nhận `aes_key` đã là `bytes`. Không cần gọi `bytes.fromhex()` nữa.
        # Việc chuyển đổi từ hex string sang bytes nên được thực hiện ở nơi gọi hàm.
        aesgcm = AESGCM(bytes.fromhex(aes_key))
        
        encrypted_private_key = aesgcm.encrypt(nonce, private_pem, None)
        encrypted_private_key_b64 = base64.b64encode(nonce + encrypted_private_key).decode('utf-8')

        # 4. Xây dựng cấu trúc dữ liệu JSON cho khoá mới
        now, expiry = datetime.now(), datetime.now() + timedelta(days=KEY_EXPIRATION_DAYS)
        new_key_data = {
            "key_id": f"{now.strftime('%Y%m%d')}_{os.urandom(4).hex()}", 
            "status": "active",
            "public_info": {"owner_email": email, "public_key_pem": public_pem.decode('utf-8'),
                            "creation_date": now.isoformat(), "expiry_date": expiry.isoformat()},
            "private_info": {"encrypted_private_key_b64": encrypted_private_key_b64}
        }
        
        # 5. Lưu file khoá mới
        new_key_path = user_dir / f"key_{new_key_number}.json"
        write_json_file(new_key_path, new_key_data)
        
        message = f"Đã tạo khoá mới thành công tại: {new_key_path.name}"
        print(message)
        return True, message

    except Exception as e:
        error_message = f"Lỗi khi xoay vòng khoá: {e}"
        print(error_message)
        return False, error_message


def check_and_manage_own_keys(email: str, aes_key: bytes):
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
    status = key_data.get("status")
    if not expiry_date_str or datetime.now() > datetime.fromisoformat(expiry_date_str) or status == "deactivated":
        print("Khoá hiện tại đã hết hạn hoặc không hợp lệ. Bắt buộc phải tạo khoá mới...")
        create_new_key(email, aes_key)
    else:
        print(f"Khoá đang hoạt động và còn hạn đến {datetime.fromisoformat(expiry_date_str).strftime('%Y-%m-%d')}.")


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
    print(aes_key)
    decrypted_pem = AESGCM(bytes.fromhex(aes_key)).decrypt(nonce, ciphertext, None)
    
    print("Đã giải mã thành công khoá riêng tư đang hoạt động.")
    return serialization.load_pem_private_key(decrypted_pem, password=None)

def get_active_public_info(email: str) -> dict | None:
    """Lấy thông tin công khai của cặp khoá đang hoạt động."""
    user_dir = get_user_dir(email)
    latest_key_path = get_latest_key_path(user_dir)
    if not latest_key_path: return None
    
    key_data = read_json_file(latest_key_path)
    return key_data.get('public_info') if key_data.get('status') == 'active' else None
