from modules.crypto.key_management import Path, get_user_dir, read_json_file,datetime, serialization, os, AESGCM, base64, write_json_file, json, get_active_private_key
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives import hashes

# Mã hóa file - gửi cho 1 đối tượng cụ thể
def encrypt_file_for_recipient(
    sender_email: str,
    recipient_email: str,
    file_stream,
    original_filename: str,
    output_dir: Path,
    merge_output: bool = True
) -> tuple[bool, str]:
    """
    Mã hoá một file cho người nhận sử dụng mã hoá lai (Hybrid Encryption).

    Args:
        sender_email (str): Email của người gửi (để tìm danh bạ).
        recipient_email (str): Email của người nhận (để tìm public key).
        file_stream: Stream của file cần mã hoá.
        original_filename (str): Tên file gốc để lưu vào metadata.
        output_dir (Path): Thư mục để lưu file kết quả.
        merge_output (bool): True để gộp thành 1 file .enc, False để tách thành .enc và .key.

    Returns:
        Một tuple (success: bool, message: str).
    """
    print(f"\n--- [MÃ HOÁ FILE '{original_filename}' CHO {recipient_email}] ---")
    try:
        # 1. Lấy public key của người nhận từ danh bạ của người gửi
        sender_user_dir = get_user_dir(sender_email)
        contacts_path = sender_user_dir / "contact_public_key.json"
        contacts = read_json_file(contacts_path)
        recipient_public_info = contacts.get(recipient_email)

        if not recipient_public_info:
            return False, f"Không tìm thấy public key cho người nhận '{recipient_email}' trong danh bạ của bạn."

        # 2. Kiểm tra hạn dùng của public key
        expiry_date_str = recipient_public_info.get("expiry_date")
        if expiry_date_str:
            if datetime.now() > datetime.fromisoformat(expiry_date_str):
                return False, f"Public key của người nhận '{recipient_email}' đã hết hạn. Vui lòng yêu cầu họ cung cấp khoá mới."

        # 3. Tải public key của người nhận thành đối tượng
        public_key_pem = recipient_public_info["public_key_pem"]
        recipient_public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))

        # --- BẮT ĐẦU QUÁ TRÌNH MÃ HOÁ LAI ---
        # 4. Sinh Ksession (AES key) ngẫu nhiên cho phiên này
        session_key = os.urandom(32)  # 256-bit AES key

        # 5. Mã hoá file bằng AES-GCM
        # GCM được ưu tiên vì nó tích hợp sẵn xác thực toàn vẹn (integrity)
        aes_nonce = os.urandom(12)  # Nonce 96-bit là tiêu chuẩn cho GCM
        aesgcm = AESGCM(session_key)
        file_content = file_stream.read()
        encrypted_file_content = aesgcm.encrypt(aes_nonce, file_content, None)

        # 6. Mã hoá Ksession (AES key) bằng RSA public key của người nhận
        encrypted_session_key = recipient_public_key.encrypt(
            session_key,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # 7. Chuẩn bị metadata
        metadata = {
            "sender_email": sender_email,
            "original_filename": original_filename,
            "timestamp_utc": datetime.utcnow().isoformat(),
            "encryption_algorithm": "AES-256-GCM",
            # Lưu các thông tin cần thiết để giải mã
            "encrypted_session_key_b64": base64.b64encode(encrypted_session_key).decode('utf-8'),
            "aes_nonce_b64": base64.b64encode(aes_nonce).decode('utf-8')
        }

        # 8. Tùy chọn lưu: gộp hoặc tách file
        if merge_output:
            # Gộp thành 1 file .enc
            # Cấu trúc: [4 bytes độ dài metadata] [metadata JSON] [Nội dung file mã hoá]
            metadata_json_bytes = json.dumps(metadata).encode('utf-8')
            metadata_len_bytes = len(metadata_json_bytes).to_bytes(4, 'big')
            
            output_path = output_dir / f"{original_filename}.enc"
            with open(output_path, 'wb') as f:
                f.write(metadata_len_bytes)
                f.write(metadata_json_bytes)
                f.write(encrypted_file_content)
            
            return True, f"Mã hoá thành công! File đã được lưu tại: {output_path}"
        else:
            # Tách thành file .key và .enc
            key_file_path = output_dir / f"{original_filename}.key"
            write_json_file(key_file_path, metadata)

            enc_file_path = output_dir / f"{original_filename}.enc"
            with open(enc_file_path, 'wb') as f:
                f.write(encrypted_file_content)

            return True, f"Mã hoá thành công! File dữ liệu và khoá đã được lưu riêng tại thư mục: {output_dir}"

    except Exception as e:
        return False, f"Đã xảy ra lỗi trong quá trình mã hoá: {e}"
    
 

def decrypt_file_from_sender(
    recipient_email: str,
    recipient_aes_key: bytes, # Khoá AES đã suy diễn từ hashed_passphrase
    enc_file_stream,
    key_file_stream=None
) -> tuple[bool, str, dict, bytes]:
    """
    Giải mã một file được mã hoá bằng mã hoá lai.

    Args:
        recipient_email (str): Email của người nhận (chính là người dùng hiện tại).
        recipient_aes_key (bytes): Khoá AES dùng để giải mã private key của người nhận.
        enc_file_stream: Stream của file .enc.
        key_file_stream (optional): Stream của file .key nếu chúng được tách riêng.

    Returns:
        Một tuple (success: bool, message: str, metadata: dict, decrypted_content: bytes).
        Nếu thất bại, metadata và decrypted_content sẽ là None.
    """
    print(f"\n--- [GIẢI MÃ FILE CHO {recipient_email}] ---")
    try:
        # --- BƯỚC 1: Lấy metadata và nội dung file đã mã hoá ---
        metadata = {}
        encrypted_file_content = b''

        if key_file_stream: # Trường hợp file .key và .enc tách riêng
            print("Phát hiện chế độ file tách rời (.key và .enc).")
            metadata = json.load(key_file_stream)
            encrypted_file_content = enc_file_stream.read()
        else: # Trường hợp file gộp
            print("Phát hiện chế độ file gộp. Đang đọc metadata...")
            # Đọc 4 bytes đầu để biết độ dài metadata
            metadata_len_bytes = enc_file_stream.read(4)
            if len(metadata_len_bytes) < 4:
                return False, "File mã hoá không hợp lệ hoặc bị hỏng (thiếu header).", None, None
            
            metadata_len = int.from_bytes(metadata_len_bytes, 'big')
            
            # Đọc metadata JSON
            metadata_json_bytes = enc_file_stream.read(metadata_len)
            metadata = json.loads(metadata_json_bytes.decode('utf-8'))
            
            # Phần còn lại của stream là nội dung file đã mã hoá
            encrypted_file_content = enc_file_stream.read()
        
        # --- BƯỚC 2: Giải mã Private Key của người nhận ---
        # Hàm này đã có sẵn, ta gọi lại nó
        private_key = get_active_private_key(recipient_email, recipient_aes_key)
        if not private_key:
            return False, "Không thể giải mã khoá riêng tư của bạn. Vui lòng kiểm tra lại.", None, None

        # --- BƯỚC 3: Giải mã Ksession (khoá AES phiên) ---
        encrypted_session_key_b64 = metadata.get('encrypted_session_key_b64')
        if not encrypted_session_key_b64:
            return False, "Metadata không chứa khoá phiên.", None, None
            
        encrypted_session_key = base64.b64decode(encrypted_session_key_b64)
        
        # Dùng private key để giải mã khoá phiên
        session_key = private_key.decrypt(
            encrypted_session_key,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # --- BƯỚC 4: Giải mã nội dung file bằng Ksession ---
        aes_nonce_b64 = metadata.get('aes_nonce_b64')
        if not aes_nonce_b64:
            return False, "Metadata không chứa nonce cho AES.", None, None

        aes_nonce = base64.b64decode(aes_nonce_b64)
        aesgcm = AESGCM(session_key)
        
        # Dùng Ksession và nonce để giải mã nội dung file
        decrypted_content = aesgcm.decrypt(aes_nonce, encrypted_file_content, None)

        print("Giải mã file thành công!")
        return True, "Giải mã file thành công!", metadata, decrypted_content

    except Exception as e:
        # Bắt các lỗi có thể xảy ra trong quá trình giải mã (sai khoá, file hỏng,...)
        return False, f"Giải mã thất bại: {e}", None, None