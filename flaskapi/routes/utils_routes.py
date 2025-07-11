from flask import Blueprint, request, render_template, jsonify, session, url_for, redirect, current_app, send_file
from modules.utils.digital_signing import digital_sign_file
from modules.utils.verify_digital_signature import verify_signature
from modules.utils.logger import log_user_action
from modules.utils.qr_code import generate_public_info_qr, process_qr_code_and_add_contact, get_all_contacts, get_user_dir
from modules.auth.logic import get_salt_from_db
from modules.crypto.key_generator import derive_aes_key
from modules.crypto.key_management import get_active_private_key

import json
import hashlib
import os
import io
from pathlib import Path
from datetime import datetime

utils_bp = Blueprint('utils', __name__)

# Requirement 8 – File Signing
@utils_bp.route('/sign_file', methods=['GET'])
def render_sign_file():
    return render_template('sign_file.html')

@utils_bp.route('/sign_file', methods=['POST'])
def signing_file_route():
    if 'user_id' not in session:
        log_user_action("Unknown", "Sign File", "Fail", "Session expired", level="warning")
        return {"success": False, "message": "You must be logged in to access this page."}, 401
    
    file = request.files.get('file_to_sign')
    email = session["email"]
    if not file or file.filename == '':
        log_user_action(email, "Sign File", "Fail", "Missing file", level="warning")
        return jsonify({'error': "No file provided."}), 400
    
    passphrase = session.get("passphrase")  
    if not passphrase:
        log_user_action(email, "Sign File", "Fail", "Missing passphrase", level="warning")
        return {"success": False, "message": "Passphrase not found."}, 401
    try:
        salt = get_salt_from_db(email)
        aes_key = derive_aes_key(passphrase, salt)
        private_key = get_active_private_key(email, aes_key)

        # Ký file và tạo file chữ ký
        sig_dict = digital_sign_file(file, private_key)
        sig_bytes = json.dumps(sig_dict, indent=2).encode('utf-8')

        signature_stream = io.BytesIO(sig_bytes)
        signature_stream.seek(0)
        
        log_user_action(email, "Sign File", "Success", f"File={file.filename}")
        return send_file(
            signature_stream,
            as_attachment=True,
            download_name=f"{file.filename}.sig",
            mimetype="application/octet-stream"
        )
    except Exception as e:
        log_user_action(email, "Sign File", "Fail", f"Error: {e}", level="error")
        return jsonify({"success": False, "message": f"Error during digital signing: {e}"}), 500


# Requirement 9 – Verify Digital Signature
@utils_bp.route('/verify_signature', methods=['GET'])
def render_verify_signature():
    return render_template('verify_signature.html')

@utils_bp.route('/verify_signature', methods=['POST'])
def verify_signature_route():
    if 'user_id' not in session:
        log_user_action("Unknown", "Verify Signature", "Fail", "Session expired", level="warning")
        return {"success": False, "message": "You must be logged in to access this page."}, 401
    
    file = request.files.get('file_to_verify')
    signature_file = request.files.get('signature')
    email = session["email"]
    
    if not file or not signature_file:
        log_user_action(email, "Verify Signature", "Fail", "Missing file or signature", level="warning")
        return jsonify({"success": False, "message": "No file or signature provided"}), 400

    if file.filename == '':
        log_user_action(email, "Verify Signature", "Fail", "Empty filename", level="warning")
        return jsonify({'error': 'Tên file trống'}), 400

    try:
        signature_json = signature_file.read().decode('utf-8')
    except Exception as e:
        log_user_action(email, "Verify Signature", "Fail", "Cannot decode signature file", level="error")
        return jsonify({"success": False, "message": "Invalid signature file format"}), 400
    
    contacts_public_key_path = get_user_dir(email) / "contact_public_key.json"

    if not os.path.exists(contacts_public_key_path):
        log_user_action(email, "Verify Signature", "Fail", "Public key file not found", level="error")
        return jsonify({"success": False, "message":  "Public key does not exist."}), 400

    # Thực hiện xác minh
    signer, signed_at = verify_signature(file, signature_json, contacts_public_key_path)
    
    dt_obj = datetime.fromisoformat(signed_at)
    formatted_timestamp = dt_obj.strftime("%Y-%m-%d %H:%M:%S") 

    if signer:
        log_user_action(email, "Verify Signature", "Success", f"Valid signature. Signed by: {signer} at {formatted_timestamp}, File={file.filename}", level="info")
        return jsonify({
            "success": True,
            "message": "Signature is valid.",
            "signer_email": signer,
            "signed_at": formatted_timestamp
        }), 200
    else:
        log_user_action(email, "Verify Signature", "Fail", f"Invalid signature, File={file.filename}", level="warning")
        return jsonify({"success": False, "message": "Signature is invalid."}), 400


# Requirement 4 – QR
@utils_bp.route("/generate_qr", methods=["GET"])
def render_generate_qr():
    if 'email' not in session:
        return redirect(url_for("auth.login"))
    
    email = session['email']
    email_hash = hashlib.sha256(email.encode()).hexdigest()
    qr_path = Path(f"data/qr/{email_hash}/my_qr.png")
    generate_public_info_qr(email, qr_path)

    return render_template("qr_code.html")

@utils_bp.route("/upload_qr", methods=["GET"])
def upload_qr():
    """
    Tạo một mã QR từ email được cung cấp qua query parameter.
    Ví dụ: /utils/generate_qr?email=user@example.com
    """

    # 1. Lấy email từ query parameter của URL
    email = session['email']

    # 2. Kiểm tra xem email có được cung cấp không
    if not email:
        # Nếu bạn có trang lỗi, có thể render nó.
        # Hoặc trả về lỗi JSON.
        log_user_action("Unknown", "Generate QR", "Fail", "Missing email in session", level="warning")
        return "Error: Please provide an email address in the URL (e.g., ?email=user@example.com)", 400

    try:
        # 3. Xác định đường dẫn output cho file QR
        # Lưu vào một thư mục tạm thời hoặc thư mục của người dùng
        user_dir = get_user_dir(email)
        qr_output_path = user_dir / f"{email.replace('@', '_at_')}_qr.png"
        print(qr_output_path)

        # 4. Gọi hàm logic để tạo file ảnh QR
        # Giả sử hàm generate_qr_image_file trả về True/False
        success, message = generate_public_info_qr(email=email, output_path=qr_output_path)

        if not success:
            # Nếu hàm tạo QR thất bại (ví dụ không tìm thấy public key)
            print(f"Lỗi khi tạo QR", message)
            # Có thể trả về một ảnh placeholder "lỗi"
            log_user_action(email, "Generate QR", "Fail", message or "QR generation failed", level="error")
            return f"Unable to generate QR code.", 500

        # 5. Gửi file ảnh vừa tạo về cho trình duyệt
        log_user_action(email, "Generate QR", "Success", f"QR generated at: {qr_output_path.name}")
        return send_file(
            ".." / qr_output_path,
            mimetype='image/png'
        )

    except Exception as e:
        log_user_action(email, "Generate QR", "Fail", f"Exception: {e}", level="error")
        return "An unknown error occurred on the server.", 500

@utils_bp.route("/qr_image/<email_hash>")
def serve_qr_image(email_hash):
    # Lấy đường dẫn tuyệt đối dựa trên thư mục gốc của app
    base_path = current_app.root_path  # VD: /Secure_Vault/flaskapi
    qr_path = os.path.join(base_path, "..", "data", "qr", email_hash, "my_qr.png")
    qr_path = os.path.abspath(qr_path)
    user_email = session.get("email", "Unknown")
    
    if not os.path.exists(qr_path):
        log_user_action(user_email, "View QR Image", "Fail", f"QR not found for hash={email_hash}", level="warning")
        return "QR code not found", 404
    log_user_action(user_email, "View QR Image", "Success", f"Served my_qr.png for hash={email_hash}")
    return send_file(qr_path, mimetype="image/png")

@utils_bp.route("/my_qr_url")
def get_qr_url():
    if 'email' not in session:
        return jsonify({"error": True, "message": "Not logged in"}), 401

    email = session['email']
    email_hash = hashlib.sha256(email.encode()).hexdigest()

    # Tạo URL từ route có thể truy cập được
    qr_url = url_for("utils.serve_qr_image", email_hash=email_hash)
    return jsonify({"qr_url": qr_url})

@utils_bp.route('/decode_qr', methods=['POST'])
def decode_qr():
    """
    Nhận một file ảnh QR, giải mã và thêm thông tin vào danh bạ
    của người dùng đang đăng nhập (lấy từ session).
    """

    # 1. Bắt đầu khối kiểm tra session
    # Kiểm tra xem người dùng đã đăng nhập hoàn toàn chưa
    if 'email' not in session:
        log_user_action("Unknown", "Decode QR", "Fail", "Not logged in", level="warning")
        return jsonify({"success": False, "message": "You are not logged in."}), 401

    # Lấy email trực tiếp từ session
    current_user_email = session.get("email")

    if not current_user_email:
        # Trường hợp hi hữu session có user_id nhưng không có email
        log_user_action("Unknown", "Decode QR", "Fail", "Session error: missing email", level="warning")
        return jsonify({"success": False, "message": "Session error."}), 401

    # --- Kết thúc khối kiểm tra session ---

    # 2. Kiểm tra file upload
    if 'qr_code_file' not in request.files:
        log_user_action(current_user_email, "Decode QR", "Fail", "No file uploaded", level="warning")
        return jsonify({"success": False, "message": "QR image not found."}), 400

    file = request.files['qr_code_file']
    if file.filename == '':
        log_user_action(current_user_email, "Decode QR", "Fail", "Empty filename", level="warning")
        return jsonify({"success": False, "message": "No file selected."}), 400

    # 3. Gọi hàm xử lý logic
    if file:
        success, message = process_qr_code_and_add_contact(
            current_user_email=current_user_email, # <-- Sử dụng biến lấy từ session
            qr_image_stream=file.stream
        )

        # 4. Flash thông báo kết quả
        if success:
            log_user_action(current_user_email, "Decode QR", "Success", f"Added contact: {message}")
            return jsonify({"success": True, "message": message}), 200
        else:
            log_user_action(current_user_email, "Decode QR", "Fail", message, level="error")
            return jsonify({"success": False, "message": message}), 400


# Requirement 13 – Check key status
# Requirement 14 – Find pub keys
@utils_bp.route("/owned_keys", methods=["GET"])
def api_get_owned_keys():
    if 'email' not in session:
        log_user_action("Unknown", "View Owned Public Keys", "Fail", "Not logged in", level="warning")
        return jsonify({"error": True, "message": "Not logged in"}), 401

    email = session['email']
    contacts = get_all_contacts(email)

    if contacts: 
        log_user_action(email, "View Owned Public Keys", "Success", f"Found {len(contacts)} keys")
        return jsonify({"success": True, "data": contacts})
    log_user_action(email, "View Owned Public Keys", "Success", "No keys found")
    return jsonify({"success": False, "data": contacts})


# Requirement 11 – Security logging
@utils_bp.route("/log_security")
def log_security():
    log_file_path = 'log/security.log'
    logs = []

    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    parts = line.strip().split(']')
                    timestamp = parts[0][1:].strip()
                    level = parts[1][2:].strip().strip('[]')
                    user = parts[2][2:].strip().strip('[]')

                    # Cắt phần nội dung Action, Status, Details
                    rest = ']'.join(parts[3:]).strip()
                    action = status = details = ""

                    for token in rest.split('|'):
                        if '=' in token:
                            key, val = token.strip().split('=', 1)
                            key = key.strip().lower()
                            val = val.strip()

                            if key == 'action':
                                action = val
                            elif key == 'status':
                                status = val
                            elif key == 'details':
                                details = val

                    logs.append({
                        "timestamp": timestamp,
                        "level": level,
                        "user": user,
                        "action": action,
                        "status": status,
                        "details": details
                    })

                except Exception as e:
                    print(f"Error parsing log line: {line}")
                    continue
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(logs)

    # Còn lại thì trả template bình thường
    return render_template("log_security.html", logs=logs)
