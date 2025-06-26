import os
import base64
from datetime import datetime, timedelta
 
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .key_extensions import get_user_dir, get_latest_key_path, write_json_file, read_json_file, Path


KEY_EXPIRATION_DAYS = 90

# Tọa khóa AES từ hash pw (sửa lại)
def derive_aes_key_from_hash(hashed_passphrase_hex: str) -> bytes:
    """Tạo khoá AES 256-bit trực tiếp từ chuỗi hex của hash SHA-256."""
    if len(hashed_passphrase_hex) != 64:
        raise ValueError("Hashed passphrase phải là một chuỗi hex 64 ký tự (SHA-256).")
    return bytes.fromhex(hashed_passphrase_hex)

# Tạo cặp khóa RSA, mã hóa pri key bằng AES Key
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
    aesgcm = AESGCM(bytes.fromhex(aes_key))
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
    return True


