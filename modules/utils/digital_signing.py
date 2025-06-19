import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa

def digital_sign_file(file, private_key_path):
    # Đọc file content dưới dạng bytes
    file_bytes = file.read()

    # Tính SHA-256 hash của file
    sha256 = hashlib.sha256(file_bytes).digest()

    # Đọc private key từ file
    with open(private_key_path, 'rb') as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )

    # Ký hash của file với private key RSA
    signature = private_key.sign(
        sha256,
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    return signature
