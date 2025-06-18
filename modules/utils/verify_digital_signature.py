import hashlib
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization

def verify_signature(file, signature, public_key_path):
    # Đọc public key từ file
    with open(public_key_path, 'rb') as f:
        public_key = serialization.load_pem_public_key(f.read())

    # Đọc nội dung file và tính hash SHA-256
    data = file.read()
    digest = hashlib.sha256(data).digest()

    try:
        # Xác minh chữ ký với public key và hash của file
        public_key.verify(
            signature, 
            digest, 
            padding.PKCS1v15(),  
            hashes.SHA256()     
        )
        return True  
    except:
        return False  
