from modules.crypto.key_generator import get_user_dir, read_json_file,datetime, serialization, os, AESGCM, base64
from modules.crypto.key_extensions import Path, write_json_file, json
from modules.crypto.key_management import get_active_private_key, hashlib
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives import hashes

# Mã hóa file - gửi cho 1 đối tượng cụ thể
CHUNK_SIZE = 1 * 1024 * 1024  # 1 MB
FILE_SIZE_THRESHOLD = 5 * 1024 * 1024 # 5 MB

def encrypt_file_for_recipient(
    sender_email: str,
    recipient_email: str,
    file_stream,
    original_filename: str,
    output_dir: Path,
    merge_output: bool = True
) -> tuple[bool, str]:
    """
    Mã hoá file. Tự động mã hóa toàn bộ cho file <= 5MB và chia khối cho file > 5MB.
    """
    print(f"\n--- [BẮT ĐẦU MÃ HOÁ '{original_filename}' CHO {recipient_email}] ---")
    try:
        # === PHẦN 1: CHUẨN BỊ KEY VÀ METADATA CHUNG ===
        # ... (logic lấy public key và sinh session key không đổi) ...
        sender_user_dir = get_user_dir(sender_email)
        contacts_path = sender_user_dir / "contact_public_key.json"
        
        if not contacts_path.exists(): 
            return False,  "Contact file not found."
        
        contacts = read_json_file(contacts_path)
        recipient_public_info = contacts.get(recipient_email)
        
        if not recipient_public_info: 
            return False, f"Public key not found for '{recipient_email}'."
        
        expiry_date_str = recipient_public_info.get("expiry_date")
        
        if expiry_date_str and datetime.now() > datetime.fromisoformat(expiry_date_str): 
            return False, f"The public key for '{recipient_email}' has expired."
        
        public_key_pem = recipient_public_info["public_key_pem"]
        recipient_public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
        session_key = os.urandom(32)
        encrypted_session_key = recipient_public_key.encrypt(
            session_key, asym_padding.OAEP(mgf=asym_padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
        
        base_metadata = {
            "sender_email": sender_email,
            "original_filename": original_filename,
            "timestamp_utc": datetime.utcnow().isoformat(),
            "algorithm": "AES-256-GCM",
            "encrypted_session_key_b64": base64.b64encode(encrypted_session_key).decode('utf-8'),
        }

        output_dir.mkdir(parents=True, exist_ok=True)
        aesgcm = AESGCM(session_key)

        # === PHẦN 2: KIỂM TRA KÍCH THƯỚC VÀ CHỌN PHƯƠNG THỨC MÃ HÓA ===
        file_stream.seek(0, 2)
        file_size = file_stream.tell()
        file_stream.seek(0)

        # --- Trường hợp 1: File lớn (> 5MB), chia khối ---
        if file_size > FILE_SIZE_THRESHOLD:
            print(f"File lớn ({file_size / 1024 / 1024:.2f} MB), tiến hành mã hoá theo khối...")
            metadata = {**base_metadata, "mode": "chunked"}

            def write_encrypted_chunks(input_stream, output_stream):
                input_stream.seek(0)
                chunk_num = 0
                while True:
                    chunk = input_stream.read(CHUNK_SIZE)
                    if not chunk: break
                    chunk_num += 1; print(f"-> Đang mã hóa khối {chunk_num}...")
                    nonce = os.urandom(12)
                    encrypted_chunk_with_tag = aesgcm.encrypt(nonce, chunk, None)
                    output_stream.write(len(encrypted_chunk_with_tag).to_bytes(4, 'big'))
                    output_stream.write(nonce)
                    output_stream.write(encrypted_chunk_with_tag)

            if merge_output:
                output_path = output_dir / f"{original_filename}.enc"
                with open(output_path, 'wb') as f_out:
                    metadata_json_bytes = json.dumps(metadata).encode('utf-8')
                    f_out.write(len(metadata_json_bytes).to_bytes(4, 'big'))
                    f_out.write(metadata_json_bytes)
                    write_encrypted_chunks(file_stream, f_out)
                return True, f"Encryption successful! File has been saved at: {output_path}"
            else:
                key_file_path = output_dir / f"{original_filename}.key"
                enc_file_path = output_dir / f"{original_filename}.enc"
                write_json_file(key_file_path, metadata)
                with open(enc_file_path, 'wb') as f_enc:
                    write_encrypted_chunks(file_stream, f_enc)
                return True, f"Encryption successful! Data file (.enc) and key file (.key) have been saved to: {output_dir}"

        # --- Trường hợp 2: File nhỏ (<= 5MB), mã hóa toàn bộ ---
        else:
            print(f"File nhỏ ({file_size / 1024:.2f} KB), tiến hành mã hoá toàn bộ...")
            nonce = os.urandom(12)
            metadata = {
                **base_metadata,
                "mode": "full",
                "aes_nonce_b64": base64.b64encode(nonce).decode('utf-8')
            }
            
            file_content = file_stream.read()
            encrypted_content = aesgcm.encrypt(nonce, file_content, None)

            if merge_output:
                output_path = output_dir / f"{original_filename}.enc"
                with open(output_path, 'wb') as f_out:
                    metadata_json_bytes = json.dumps(metadata).encode('utf-8')
                    f_out.write(len(metadata_json_bytes).to_bytes(4, 'big'))
                    f_out.write(metadata_json_bytes)
                    f_out.write(encrypted_content)
                return True, f"Encryption successful! File has been saved at: {output_path}"
            else:
                key_file_path = output_dir / f"{original_filename}.key"
                enc_file_path = output_dir / f"{original_filename}.enc"
                write_json_file(key_file_path, metadata)
                with open(enc_file_path, 'wb') as f_enc:
                    f_enc.write(encrypted_content)
                return True, f"Encryption successful! Data file (.enc) and key file (.key) have been saved to: {output_dir}"

    except Exception as e:
        return False, f"An error occurred during encryption: {e}"

# --- HÀM GIẢI MÃ ĐÃ ĐƯỢC CẬP NHẬT ---
def decrypt_file_from_sender(
    recipient_email: str,
    recipient_aes_key: bytes,
    enc_file_stream,
    output_dir: Path,
    key_file_stream=None
) -> tuple[bool, str, dict, bytes]:
    """
    Giải mã file. Tự động nhận diện chế độ mã hóa (toàn bộ hoặc chia khối).
    """
    mode_str = "TÁCH RỜI" if key_file_stream else "GỘP"
    print(f"\n--- [GIẢI MÃ FILE CHO {recipient_email} - Chế độ: {mode_str}] ---")
    
    output_file_path = None
    try:
        # === BƯỚC 1: LẤY METADATA VÀ GIẢI MÃ SESSION KEY (Không đổi) ===
        if key_file_stream:
            metadata = json.load(key_file_stream)
        else:
            metadata_len_bytes = enc_file_stream.read(4)
            if len(metadata_len_bytes) < 4: raise ValueError("File gộp không hợp lệ.")
            metadata_len = int.from_bytes(metadata_len_bytes, 'big')
            metadata = json.loads(enc_file_stream.read(metadata_len))

        private_key = get_active_private_key(recipient_email, recipient_aes_key)
        if not private_key: raise ValueError("Không thể giải mã khoá riêng tư.")
        encrypted_session_key_b64 = metadata['encrypted_session_key_b64']
        encrypted_session_key = base64.b64decode(encrypted_session_key_b64)
        session_key = private_key.decrypt(
            encrypted_session_key, asym_padding.OAEP(mgf=asym_padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
        aesgcm = AESGCM(session_key)
        decrypted_content = b''

        # === BƯỚC 2: KIỂM TRA CHẾ ĐỘ VÀ GIẢI MÃ TƯƠNG ỨNG ===
        encryption_mode = metadata.get("mode", "chunked") # Mặc định là 'chunked' cho file cũ
        
        # --- Chế độ 1: Giải mã file được chia khối ---
        if encryption_mode == "chunked":
            print("Phát hiện chế độ mã hóa chia khối (chunked).")
            decrypted_chunks = []
            chunk_num = 0
            while True:
                chunk_len_bytes = enc_file_stream.read(4)
                if not chunk_len_bytes: break
                chunk_num += 1; print(f"-> Đang giải mã khối {chunk_num}...")
                encrypted_len = int.from_bytes(chunk_len_bytes, 'big')
                nonce = enc_file_stream.read(12)
                encrypted_chunk_with_tag = enc_file_stream.read(encrypted_len)
                decrypted_chunk = aesgcm.decrypt(nonce, encrypted_chunk_with_tag, None)
                decrypted_chunks.append(decrypted_chunk)
            decrypted_content = b"".join(decrypted_chunks)
            
        # --- Chế độ 2: Giải mã file toàn bộ ---
        elif encryption_mode == "full":
            print("Phát hiện chế độ mã hóa toàn bộ (full).")
            nonce_b64 = metadata.get("aes_nonce_b64")
            if not nonce_b64: raise ValueError("Metadata thiếu nonce cho chế độ mã hóa toàn bộ.")
            nonce = base64.b64decode(nonce_b64)
            encrypted_data = enc_file_stream.read()
            decrypted_content = aesgcm.decrypt(nonce, encrypted_data, None)
        else:
            raise ValueError(f"Encryption mode '{encryption_mode}' is not supported.")

        # === BƯỚC 3: GHI FILE VÀ TRẢ VỀ KẾT QUẢ (Không đổi) ===
        original_filename = metadata.get("original_filename", "decrypted_file.dat")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file_path = output_dir / original_filename
        print(f"Ghi nội dung đã giải mã vào file '{original_filename}'...")
        with open(output_file_path, "wb") as f_out:
            f_out.write(decrypted_content)
        message = f"Decryption successful! File '{original_filename}' has been saved at: {output_file_path}"
        print(message)
        return True, message, metadata, decrypted_content

    except Exception as e:
        if output_file_path and output_file_path.exists():
            output_file_path.unlink()
        return False, f"Decryption failed: {e}", locals().get('metadata'), None