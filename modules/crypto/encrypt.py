from modules.crypto.key_generator import get_user_dir, read_json_file,datetime, serialization, os, AESGCM, base64
from modules.crypto.key_extensions import Path, write_json_file, json
from modules.crypto.key_management import get_active_private_key, hashlib
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
        print("Hello")
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
            print("Hello")

            # Tách thành file .key và .enc
            output_dir.mkdir(exist_ok=True)
            key_file_path = output_dir / f"{original_filename}.key"
            
            write_json_file(key_file_path, metadata)
            print("hello")            


            enc_file_path = output_dir / f"{original_filename}.enc"
            with open(enc_file_path, 'wb') as f:
                f.write(encrypted_file_content)

            return True, f"Mã hoá thành công! File dữ liệu và khoá đã được lưu riêng tại thư mục: {output_dir}"

    except Exception as e:
        return False, f"Đã xảy ra lỗi trong quá trình mã hoá: {e}"
    

def decrypt_file_from_sender(
    recipient_email: str,
    recipient_aes_key: bytes,
    enc_file_stream,
    output_dir: Path, # <-- THAM SỐ MỚI
    key_file_stream=None
) -> tuple[bool, str, dict, bytes]:
    """
    Giải mã một file và tự động lưu kết quả vào một thư mục.

    Args:
        ... (các tham số cũ) ...
        output_dir (Path): Thư mục để lưu file đã giải mã.

    Returns:
        Một tuple (success: bool, message: str, metadata: dict, decrypted_content: bytes).
        decrypted_content vẫn được trả về để có thể gửi ngay cho người dùng.
    """
    print(f"\n--- [GIẢI MÃ FILE CHO {recipient_email}] ---")
    try:
        # --- BƯỚC 1: Lấy metadata và nội dung file đã mã hoá ---
        metadata = {}
        encrypted_file_content = b''

        if key_file_stream:
            metadata = json.load(key_file_stream)
            encrypted_file_content = enc_file_stream.read()
        else:
            metadata_len_bytes = enc_file_stream.read(4)
            if len(metadata_len_bytes) < 4:
                return False, "File mã hoá không hợp lệ hoặc bị hỏng (thiếu header).", None, None
            metadata_len = int.from_bytes(metadata_len_bytes, 'big')
            metadata_json_bytes = enc_file_stream.read(metadata_len)
            metadata = json.loads(metadata_json_bytes.decode('utf-8'))
            encrypted_file_content = enc_file_stream.read()
        
        # --- BƯỚC 2 & 3: Giải mã Private Key và Ksession ---
        private_key = get_active_private_key(recipient_email, recipient_aes_key)
        if not private_key:
            return False, "Không thể giải mã khoá riêng tư của bạn.", None, None

        encrypted_session_key_b64 = metadata.get('encrypted_session_key_b64')
        if not encrypted_session_key_b64:
            return False, "Metadata không chứa khoá phiên.", None, None
        
        encrypted_session_key = base64.b64decode(encrypted_session_key_b64)
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
        decrypted_content = aesgcm.decrypt(aes_nonce, encrypted_file_content, None)
        
        # --- BƯỚC 5: LƯU FILE ĐÃ GIẢI MÃ (THAY ĐỔI Ở ĐÂY) ---
        original_filename = metadata.get("original_filename", "decrypted_file.dat")
        
        # Đảm bảo thư mục output tồn tại
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Tạo đường dẫn file output
        output_dir.mkdir(exist_ok=True)
        output_file_path = output_dir / original_filename
        
        # Ghi nội dung đã giải mã vào file
        with open(output_file_path, "wb") as f:
            f.write(decrypted_content)
        
        print(f"Giải mã và lưu file thành công tại: {output_file_path}")
        
        # Trả về thông báo thành công cùng với các dữ liệu khác
        message = f"Giải mã thành công và đã lưu file '{original_filename}'."
        return True, message, metadata, decrypted_content

    except Exception as e:
        return False, f"Giải mã thất bại: {e}", None, None
