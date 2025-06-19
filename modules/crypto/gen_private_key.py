from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import os

def generate_keypair():
    # Tạo private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # Lưu private key vào file
    private_key_path = "data/keys/private.pem"
    with open(private_key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

    print(f"✅ Đã tạo private key tại {private_key_path}")

    # Tạo public key từ private key
    public_key = private_key.public_key()

    # Lưu public key vào file
    public_key_path = "data/keys/public.pem"
    with open(public_key_path, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

    print(f"✅ Đã tạo public key tại {public_key_path}")

# Gọi hàm tạo key pair
generate_keypair()
