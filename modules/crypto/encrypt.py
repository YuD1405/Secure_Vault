from modules.crypto.gen_private_key import Path, get_user_dir, read_json_file,datetime, serialization, os, AESGCM, base64, write_json_file, json
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives import hashes


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