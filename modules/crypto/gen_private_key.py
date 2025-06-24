
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

def create_new_key(email: str, aes_key: bytes):
    """Tạo một cặp khoá RSA mới, mã hoá và lưu trữ nó."""
    user_dir = get_user_dir(email)
    
    # 1. Huỷ kích hoạt khoá cũ (nếu có)
    latest_key_path = get_latest_key_path(user_dir)
    new_key_number = 1
    if latest_key_path:
        key_data = read_json_file(latest_key_path)
        key_data['status'] = 'deactivated'
        write_json_file(latest_key_path, key_data)
        latest_key_number = int(latest_key_path.stem.split('_')[1])
        new_key_number = latest_key_number + 1
        print(f"Đã huỷ kích hoạt khoá cũ: {latest_key_path.name}")

    # 2. Tạo cặp khoá RSA mới
    private_key_obj = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key_obj = private_key_obj.public_key()
    
    private_pem = private_key_obj.private_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_pem = public_key_obj.public_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # 4. Mã hoá private key
    nonce = os.urandom(12)
    aesgcm = AESGCM(aes_key)
    encrypted_private_key = aesgcm.encrypt(nonce, private_pem, None)
    encrypted_private_key_b64 = base64.b64encode(nonce + encrypted_private_key).decode('utf-8')

    # 5. Xây dựng cấu trúc dữ liệu JSON
    now, expiry = datetime.now(), datetime.now() + timedelta(days=KEY_EXPIRATION_DAYS)
    new_key_data = {
        "key_id": f"{now.strftime('%Y%m%d')}_{os.urandom(4).hex()}", "status": "active",
        "public_info": {"owner_email": email, "public_key_pem": public_pem.decode('utf-8'),
                        "creation_date": now.isoformat(), "expiry_date": expiry.isoformat()},
        "private_info": {"encrypted_private_key_b64": encrypted_private_key_b64}
    }
    
    # 6. Lưu file mới
    new_key_path = user_dir / f"key_{new_key_number}.json"
    write_json_file(new_key_path, new_key_data)
    print(f"Đã tạo và lưu khoá mới thành công tại: {new_key_path.name}")


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
    
    if not expiry_date_str or datetime.now() > datetime.fromisoformat(expiry_date_str):
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
    
    decrypted_pem = AESGCM(aes_key).decrypt(nonce, ciphertext, None)
    
    print("Đã giải mã thành công khoá riêng tư đang hoạt động.")
    return serialization.load_pem_private_key(decrypted_pem, password=None)

def get_active_public_info(email: str) -> dict | None:
    """Lấy thông tin công khai của cặp khoá đang hoạt động."""
    user_dir = get_user_dir(email)
    latest_key_path = get_latest_key_path(user_dir)
    if not latest_key_path: return None
    
    key_data = read_json_file(latest_key_path)
    return key_data.get('public_info') if key_data.get('status') == 'active' else None

def generate_public_info_qr(email: str, output_path: str | Path):
    """Tạo mã QR chứa thông tin công khai của khoá đang hoạt động."""
    import qrcode # import tại đây để không bắt buộc phải cài nếu không dùng đến
    print("\n--- [TẠO QR CODE CHO PUBLIC KEY] ---")
    public_info = get_active_public_info(email)
    if not public_info:
        print("Lỗi: Không thể tạo QR code vì không có khoá nào đang hoạt động.")
        return

    public_key_b64 = base64.b64encode(public_info["public_key_pem"].encode()).decode()
    qr_data = {"email": public_info["owner_email"], "creation_date": public_info["creation_date"],
               "public_key_b64": public_key_b64}
    
    json_string = json.dumps(qr_data, separators=(',', ':'))
    img = qrcode.make(json_string)
    img.save(output_path)
    print(f"Đã tạo và lưu QR code thành công tại: {output_path}")



def add_contact_public_key(user_dir: Path, contact_email: str, public_info: dict):
    """Tiện ích để lưu trữ public_info của một người dùng khác vào danh bạ."""
    contacts_path = user_dir / "contact_public_key.json"
    contacts_data = read_json_file(contacts_path)
    
    contacts_data[contact_email] = public_info
    
    write_json_file(contacts_path, contacts_data)
    print(f"Đã thêm/cập nhật public key của '{contact_email}' vào danh bạ.")

def process_qr_code_and_add_contact(current_user_email: str, qr_image_stream) -> tuple[bool, str]:
    """
    Đọc một file ảnh QR, giải mã nội dung, xác thực và lưu vào danh bạ.

    Args:
        current_user_email (str): Email của người dùng đang đăng nhập (để biết lưu vào thư mục nào).
        qr_image_stream: Một đối tượng file-like stream của ảnh được upload.

    Returns:
        Một tuple (success: bool, message: str).
    """
    try:
        # 1. Đọc ảnh từ stream sử dụng OpenCV
        # Đọc stream vào một numpy array
        import numpy as np
        image_array = np.frombuffer(qr_image_stream.read(), np.uint8)
        # Decode array thành ảnh mà OpenCV có thể đọc
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if img is None:
            return False, "Không thể đọc file ảnh. Vui lòng thử lại với định dạng khác (PNG, JPG)."

        # 2. Giải mã QR code từ ảnh
        decoded_objects = qr_decode(img)
        if not decoded_objects:
            return False, "Không tìm thấy mã QR nào trong ảnh."

        # 3. Lấy dữ liệu và phân tích cú pháp JSON
        qr_data_string = decoded_objects[0].data.decode('utf-8')
        qr_data = json.loads(qr_data_string)

        # 4. Xác thực dữ liệu cơ bản
        contact_email = qr_data.get('email')
        creation_date = qr_data.get('creation_date')
        public_key_b64 = qr_data.get('public_key_b64')

        if not all([contact_email, creation_date, public_key_b64]):
            return False, "Dữ liệu từ QR code không đầy đủ hoặc không hợp lệ."
            
        if contact_email == current_user_email:
            return False, "Bạn không thể thêm chính mình vào danh bạ."

        # 5. Giải mã Base64 để lấy public key PEM
        try:
            public_key_pem = base64.b64decode(public_key_b64).decode('utf-8')
        except Exception:
            return False, "Định dạng public key trong QR code không hợp lệ."
            
        # 6. Tạo đối tượng public_info để lưu trữ
        # Ở đây chúng ta không có expiry_date từ QR, có thể để trống hoặc tính toán
        # nếu có quy tắc nào đó. Tạm thời để trống.
        public_info_to_save = {
            "owner_email": contact_email,
            "public_key_pem": public_key_pem,
            "creation_date": creation_date,
            "expiry_date": None  # Không có thông tin này từ QR
        }

        # 7. Lấy thư mục của người dùng hiện tại và lưu contact
        user_dir = get_user_dir(current_user_email)
        add_contact_public_key(user_dir, contact_email, public_info_to_save)
        
        return True, f"Đã thêm thành công {contact_email} vào danh bạ của bạn!"

    except json.JSONDecodeError:
        return False, "Nội dung QR code không phải là định dạng JSON hợp lệ."
    except Exception as e:
        return False, f"Đã xảy ra lỗi không xác định: {e}"