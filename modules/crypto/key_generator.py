import os
import base64
from datetime import datetime, timedelta
 
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

from modules.crypto.key_extensions import get_user_dir, get_latest_key_path, write_json_file, read_json_file, Path

KEY_EXPIRATION_DAYS = 90

# Tọa khóa AES từ pw
def derive_aes_key(passphrase: str, salt: str, iterations: int = 100_000) -> bytes:
    """
    Tạo khóa AES 256-bit từ passphrase thô (dạng string), dùng thuật toán PBKDF2-HMAC-SHA256.
    
    Args:
        passphrase (str): Passphrase dạng thô người dùng nhập.
        salt (bytes): Salt ngẫu nhiên hoặc cố định (16–32 byte).
        iterations (int): Số vòng lặp để tăng độ mạnh (mặc định: 100_000).
        
    Returns:
        bytes: Khóa AES 32 byte.
    """
    if isinstance(salt, memoryview):
        salt = salt.tobytes()
    elif isinstance(salt, str):
        salt = salt.encode('utf-8')
    elif isinstance(salt, bytearray):
        salt = bytes(salt)
        
    if not isinstance(passphrase, str):
        raise TypeError("Passphrase must be a string.")
    if not isinstance(salt, bytes):
        raise TypeError("Salt must be bytes.")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # AES-256
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    return kdf.derive(passphrase.encode('utf-8'))

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
    aesgcm = AESGCM(aes_key)
    encrypted_private_key = aesgcm.encrypt(nonce, private_pem, None)
    encrypted_private_key_b64 = base64.b64encode(nonce + encrypted_private_key).decode('utf-8')

    # Tạo 1 file lưu private key mã hóa bằng aes key derive từ recovery code và lưu file trong folder hash email với tên "key_recovery"
    
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