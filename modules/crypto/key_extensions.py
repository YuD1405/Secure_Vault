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
