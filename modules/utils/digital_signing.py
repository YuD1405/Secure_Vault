import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from modules.utils.logger import log_internal_event
import os

def digital_sign_file(file, private_key):
    """
    Function: digital_sign_file(file, private_key_path)

    Description:
        This function performs digital signing of a file by first computing a SHA-256 hash
        of the file content and then signing that hash using an RSA private key.

    Procedure:
        1. Reads the entire content of the input file as bytes.
        2. Computes the SHA-256 hash of the file content.
        3. Loads the RSA private key from a PEM-formatted file.
        4. Signs the hash using RSA with PKCS#1 v1.5 padding and SHA-256.
        5. Returns the digital signature in raw byte format.

    Parameters:
        file (file object): The file to be signed, opened in 'rb' (read-binary) mode.
        private_key_path (str): Path to the PEM file containing the RSA private key.

    Returns:
        signature (bytes): The digital signature generated from the file.
    """
    
    file.seek(0)
    file_bytes = file.read()

    # Tính SHA-256 hash của file
    sha256 = hashlib.sha256(file_bytes).digest()

    # Ký hash của file với private key RSA
    signature = private_key.sign(
        sha256,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    
        # Ghi file chữ ký
    sig_folder = "data/signature"
    os.makedirs(sig_folder, exist_ok=True)
    sig_path = os.path.join(sig_folder, file.filename + ".sig")
    with open(sig_path, 'wb') as sig_file:
        sig_file.write(signature)
        
    log_internal_event("digital_signature", f"Signed {file.filename} successfully and saved to {sig_folder}.")
    
    return signature
