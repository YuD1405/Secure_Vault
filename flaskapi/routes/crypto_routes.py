from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, make_response, jsonify
import os
import io
import zipfile

from modules.crypto.key_management import get_all_key_strings, check_and_manage_own_keys
from modules.crypto.key_generator import create_new_key, derive_aes_key
from modules.crypto.encrypt import encrypt_file_for_recipient, decrypt_file_from_sender
from modules.crypto.key_extensions import get_user_dir, Path
from modules.auth.logic import get_salt_from_db

crypto_bp = Blueprint('crypto', __name__)

# Requirement 3 – RSA key managements
@crypto_bp.route("/render_manage_keys", methods=['GET'])
def render_manage_keys():
    return render_template("manage_keys.html")

# Hàm để lấy toàn bộ keys (pri + pub + exp) của người dùng => bảng toàn bộ key người dùng trên fe
@crypto_bp.route("/manage_keys", methods=['GET'])
def manage_keys():
    if 'user_id' not in session:
        return {"success": False, "message":  "You must be logged in to access this page."}, 401

    email = session["email"]
    passphrase = session.get("passphrase")  
    if not passphrase:
        return {"success": False, "message":"Passphrase not found."}, 401

    try:
        salt = get_salt_from_db(email)
        key = derive_aes_key(passphrase, salt)
    except Exception as e:
        return {"success": False, "message": f"Error generating AES key: {e}"}, 400

    try:
        check_and_manage_own_keys(email, key)
        all_keys = get_all_key_strings(email)
        return jsonify({"success": True, "keys": all_keys})
    except Exception as e:
        return {"success": False, "message": f"Error retrieving key list: {e}"}, 500

# Hàm để tạo key mới và deactivate các key cũ => nút tạo key mới trên fe
@crypto_bp.route("/regenerate_key", methods=["POST"])
def regenerate_key():
    if 'user_id' not in session:
        return {"success": False, "message": "Session has expired."}, 401

    email = session["email"]
    passphrase = session.get("passphrase")
    if not passphrase:
        session.clear()
        return {"success": False, "message": "Passphrase not found."}, 401

    try:
        salt = get_salt_from_db(email)
        aes_key = derive_aes_key(passphrase, salt)
    except Exception as e:
        session.clear()
        return {"success": False, "message": f"Error during key generation: {e}"}, 400

    success = create_new_key(email, aes_key)
    if success:
        return {"success": True, "message":  "New key pair generated successfully."}
    else:
        return {"success": False, "message": "Key generation failed."}, 500

# Requirement 6 – Encrypt
@crypto_bp.route('/render_encrypt', methods=['GET'])
def render_encrypt():
    return render_template('encrypt.html')

@crypto_bp.route("/encrypt_file", methods=['POST'])
def encrypt_file():
    """
    Nhận file từ client, mã hoá cho người nhận, và trả về file kết quả (.enc hoặc .zip) hoặc JSON nếu lỗi.
    """
    if 'user_id' not in session:
        return {"success": False, "message": "Session has expired."}, 401

    sender_email = session["email"]
    recipient_email = request.form.get('recipient_email')
    file_to_encrypt = request.files.get('file_to_encrypt')
    output_option = request.form.get('output_option')

    if not file_to_encrypt or not recipient_email or file_to_encrypt.filename == '':
        return {"success": False, "message":  "Please select a file and enter the recipient's email address."}, 400

    output_dir = get_user_dir(sender_email) / "encrypted_outputs"
    output_dir.mkdir(exist_ok=True)
    merge_output = (output_option == 'combined')

    success, message = encrypt_file_for_recipient(
        sender_email=sender_email,
        recipient_email=recipient_email,
        file_stream=file_to_encrypt.stream,
        original_filename=file_to_encrypt.filename,
        output_dir=output_dir,
        merge_output=merge_output
    )

    if not success:
        return {"success": False, "message": f"Encryption failed: {message}"}, 400

    try:
        original_filename = file_to_encrypt.filename
        original_filename_base = Path(original_filename).stem

        if merge_output:
            encrypted_file_path = output_dir / f"{original_filename}.enc"

            if not encrypted_file_path.exists():
                return {"success": False, "message": "Encrypted .enc file not found."}, 500

            return send_file(encrypted_file_path.resolve(strict=True), as_attachment=True)

        else:
            enc_file_path = output_dir / f"{original_filename}.enc"
            key_file_path = output_dir / f"{original_filename}.key"

            if not (enc_file_path.exists() and key_file_path.exists()):
                return {"success": False, "message": "Failed to generate complete encrypted file."}, 500

            memory_file = io.BytesIO()
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(enc_file_path, arcname=enc_file_path.name)
                zf.write(key_file_path, arcname=key_file_path.name)
            memory_file.seek(0)

            return send_file(
                memory_file,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f"{original_filename_base}_encrypted.zip"
            )

    except Exception as e:
        return {"success": False, "message": f"An internal error occurred: {e}"}, 500

# Requirement 7 – Decrypt
@crypto_bp.route('/render_decrypt', methods=['GET'])
def render_decrypt():
    return render_template('decrypt.html')

# Hàm gọi module decrypt , js sẽ truyền xuống 1 file > trả về 1 file đã giải mã để fe xử lí download
@crypto_bp.route("/decrypt", methods=['POST'])
def decrypt_file():
    if 'user_id' not in session:
        return {"success": False, "message":  "Session has expired."}, 401

    recipient_email = session["email"]
    passphrase = session.get('passphrase')
    if not passphrase:
        return {"success": False, "message": "Session error"}, 401

    try:
        salt = get_salt_from_db(recipient_email)
        aes_key = derive_aes_key(passphrase, salt)
    except Exception as e:
        return {"success": False, "message": f"Error generating AES key: {e}"}, 400

    uploaded_file = request.files.get('file_to_decrypt')
    if not uploaded_file or uploaded_file.filename == '':
        return {"success": False, "message": "Please select a .enc or .zip file."}, 400

    filename = uploaded_file.filename
    enc_file_stream = None
    key_file_stream = None

    output_dir = get_user_dir(recipient_email) / "decrypted_outputs"
    
    try:
        if filename.lower().endswith('.zip'):
            with zipfile.ZipFile(uploaded_file.stream, 'r') as zf:
                for name in zf.namelist():
                    if name.lower().endswith('.enc'):
                        enc_file_stream = io.BytesIO(zf.read(name))
                    elif name.lower().endswith('.key'):
                        key_file_stream = io.BytesIO(zf.read(name))
            if not enc_file_stream or not key_file_stream:
                return {"success": False, "message":  "The ZIP archive does not contain both .enc and .key files."}, 400

        elif filename.lower().endswith('.enc'):
            enc_file_stream = uploaded_file.stream
        else:
            return {"success": False, "message": "Invalid file. Only .enc and .zip formats are supported."}, 400
        print("Oke")
        success, message, metadata, decrypted_content = decrypt_file_from_sender(
            recipient_email=recipient_email,
            recipient_aes_key=aes_key,
            enc_file_stream=enc_file_stream,
            output_dir = output_dir,
            key_file_stream=key_file_stream
        )
        if success:
            original_filename = metadata.get('original_filename', 'decrypted_file.dat')
            response = make_response(decrypted_content)
            response.headers.set('Content-Type', 'application/octet-stream')
            response.headers.set('Content-Disposition', 'attachment', filename=original_filename)
            return response
        else:
            return {"success": False, "message": message}, 400

    except zipfile.BadZipFile:
        return {"success": False, "message": "Corrupted ZIP file."}, 400
    except Exception as e:
        return {"success": False, "message": f"Internal error: {e}"}, 500
