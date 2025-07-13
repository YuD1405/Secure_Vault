import os
import json
import hashlib
import base64
import cv2
from datetime import datetime, timedelta
from pathlib import Path
 
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_DIR = Path("data/key_manage")

def get_user_dir(email: str) -> Path:
    """Lấy đường dẫn thư mục của người dùng dựa trên hash email."""
    email_hash = hashlib.sha256(email.encode('utf-8')).hexdigest()
    user_dir = KEY_DIR / email_hash
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir

def get_key_files(user_dir: Path) -> list[Path]:
    """Lấy danh sách các file key của người dùng, sắp xếp theo số thứ tự."""
    files = [
        f for f in user_dir.glob("key_*.json")
        if f.stem != "key_0" and f.stem.split('_')[1].isdigit()
    ]
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

# Tạo file tmp theo email
def save_temp_private_key(email: str, private_key_pem: bytes):
    tmp_path = Path("data/temp_keys") / f"{email}_recovery.pem"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_bytes(private_key_pem)
    
def read_temp_private_key(email: str):
    tmp_path = Path("data/temp_keys") / f"{email}_recovery.pem"
    
    if not tmp_path.exists():
        raise FileNotFoundError(f"Temporary private key not found for {email}")
    
    key_data = tmp_path.read_bytes()

    try:
        tmp_path.unlink()
    except Exception as e:
        print(f"[Warning] Failed to delete temporary private key file: {e}")
    
    return key_data

# Ghi và đọc recovery code vào file tạm
def write_temp_recovery_code(email: str, recovery_code: str):
    """
    Ghi recovery code tạm thời vào file để dùng lại trong reset_password.
    File sẽ nằm trong thư mục: data/temp_keys/<email>_recovery_code.txt
    """
    tmp_dir = Path("data/temp_keys")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    file_path = tmp_dir / f"{email}_recovery_code.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(recovery_code)
        
def read_temp_recovery_code(email: str) -> str:
    """
    Đọc recovery code tạm từ file rồi xoá luôn file sau khi đọc.
    """
    file_path = Path("data/temp_keys") / f"{email}_recovery_code.txt"
    if not file_path.exists():
        raise FileNotFoundError(f"Recovery code file not found for {email}")
    
    code = file_path.read_text(encoding="utf-8").strip()

    try:
        file_path.unlink()  # Xoá sau khi đọc
    except Exception as e:
        print(f"[Warning] Cannot delete temporary recovery code file: {e}")

    return code
