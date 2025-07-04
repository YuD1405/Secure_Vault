import hashlib
import json
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from modules.utils.logger import log_internal_event


def verify_signature(file, signature: bytes, contacts_json_path: str):
    """
    Dò toàn bộ public key từ file JSON và xác minh chữ ký.
    Trả về True nếu hợp lệ với bất kỳ key nào.
    """
    try:
        with open(contacts_json_path, "r", encoding="utf-8") as f:
            contact_data = json.load(f)
    except Exception as e:
        print(f"[verify_signature] Lỗi khi đọc JSON: {e}")
        return False

    file.seek(0)
    file_data = file.read()
    file_hash = hashlib.sha256(file_data).digest()

    for email, info in contact_data.items():
        public_pem = info.get("public_key_pem")
        if not public_pem:
            continue  # Bỏ qua nếu không có key

        try:
            public_key = serialization.load_pem_public_key(public_pem.encode('utf-8'))

            # Thử xác minh chữ ký
            public_key.verify(
                signature,
                file_hash,
                padding.PKCS1v15(),
                hashes.SHA256()
            )

            print(f"[verify_signature] Chữ ký hợp lệ. Người ký: {email}")
            log_internal_event("digital_signature", f"Verified signature for {file.filename} successfully.")
            return email

        except Exception as e:
            # Tiếp tục thử key khác
            continue
    
    log_internal_event("digital_signature", f"Failed to verify signature for {file.filename}.", level="warning")
    return None