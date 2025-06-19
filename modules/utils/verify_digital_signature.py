import hashlib
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from modules.utils.logger import log_internal_event

def verify_signature(file, signature, public_key_path):
    """
    Function: verify_signature(file, signature, public_key_path)

    Description:
        This function verifies a digital signature for a given file using the corresponding RSA public key.
        It ensures that the file has not been tampered with and confirms the authenticity of the signer.

    Procedure:
        1. Reads the entire content of the input file as bytes.
        2. Computes the SHA-256 hash of the file content.
        3. Loads the RSA public key from a PEM-formatted file.
        4. Verifies the provided signature against the computed hash using the RSA public key
        with PKCS#1 v1.5 padding and SHA-256.

    Parameters:
        file (file object): The file whose signature is to be verified, opened in 'rb' mode.
        signature (bytes): The digital signature to be verified (must match what was generated during signing).
        public_key_path (str): Path to the PEM file containing the RSA public key.

    Returns:
        bool: True if the signature is valid and matches the file's hash, False otherwise.
    """
    
    # Đọc public key từ file
    with open(public_key_path, 'rb') as f:
        public_key = serialization.load_pem_public_key(f.read())

    # Đọc nội dung file và tính hash SHA-256
    file.seek(0)
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
        log_internal_event("digital_signature", f"Verified signature for {file.filename} successfully.")
        return True  
    except:
        log_internal_event("digital_signature", f"Failed to verify signature for {file.filename}.", level="warning")
        return False  
