from flask import Blueprint, request, render_template, jsonify
from modules.utils.digital_signing import digital_sign_file
from modules.utils.verify_digital_signature import verify_signature
from modules.utils.logger import log_user_action
import os

utils_bp = Blueprint('utils', __name__)

# Requirement 8 – File Signing
@utils_bp.route('/sign_file', methods=['GET'])
def render_sign_file():
    return render_template('sign_file.html')

@utils_bp.route('/sign_file', methods=['POST'])
def signing_file_route():
    file = request.files.get('file_to_sign')

    if not file:
        log_user_action("anonymous", "Sign file", "Failure", "Missing file", level="warning")
        return jsonify({'error': 'Không có file nào'}), 400

    if file.filename == '':
        log_user_action("anonymous", "Sign file", "Failure", "Empty filename", level="warning")
        return jsonify({'error': 'Tên file trống'}), 400

    private_key_path = 'data/keys/private.pem'
    if not os.path.exists(private_key_path):
        log_user_action("anonymous", "Sign file", "Failure", "Private key not found", level="error")
        return jsonify({'error': 'Không tìm thấy private key!'}), 500

    # Thực hiện ký số và lưu
    signature = digital_sign_file(file, private_key_path)

    log_user_action("anonymous", "Sign file", "Success", f"File: {file.filename}", level="info")
    return jsonify({'message': 'Đã ký số thành công!'})

# Requirement 9 – Verify Digital Signature
@utils_bp.route('/verify_signature', methods=['GET'])
def render_verify_signature():
    return render_template('verify_signature.html')

@utils_bp.route('/verify_signature', methods=['POST'])
def verify_signature_route():
    file = request.files.get('file_to_verify')
    signature_file = request.files.get('signature')

    if not file or not signature_file:
        log_user_action("anonymous", "Verify signature", "Failure", "Missing file or signature", level="warning")
        return jsonify({"success": False, "message": "No file or signature provided"}), 400

    if file.filename == '':
        log_user_action("anonymous", "Verify signature", "Failure", "Empty filename", level="warning")
        return jsonify({'error': 'Tên file trống'}), 400

    signature = signature_file.read()
    public_key_path = request.form.get('public_key_path', 'data/keys/public.pem')

    if not os.path.exists(public_key_path):
        log_user_action("anonymous", "Verify signature", "Failure", "Public key not found", level="error")
        return jsonify({"success": False, "message": "Public key không tồn tại"}), 400

    # Thực hiện xác minh
    is_valid = verify_signature(file, signature, public_key_path)

    if is_valid:
        log_user_action("anonymous", "Verify signature", "Success", f"File: {file.filename}", level="info")
        return jsonify({"success": True, "message": "Signature is valid."}), 200
    else:
        log_user_action("anonymous", "Verify signature", "Failure", f"File: {file.filename}", level="warning")
        return jsonify({"success": False, "message": "Signature is invalid."}), 400

# Placeholder routes
@utils_bp.route("/generate_qr")
def generate_qr():
    return "Gen Qr"

# Requirement 11 – Security logging
@utils_bp.route("/log_security")
def log_security():
    log_file_path = 'log/security.log'
    logs = []

    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as f:
            for line in f:
                try:
                    # Format: [timestamp] [LEVEL]: [user] Action: ... | Status: ... | File: ...
                    time_start = line.find('[') + 1
                    time_end = line.find(']')
                    timestamp = line[time_start:time_end]

                    level_start = line.find('[', time_end + 1) + 1
                    level_end = line.find(']', level_start)
                    level = line[level_start:level_end]

                    user_start = line.find('[', level_end + 1) + 1
                    user_end = line.find(']', user_start)
                    user = line[user_start:user_end]

                    # Nội dung còn lại
                    rest = line[user_end + 2:].strip()

                    # Tách các trường còn lại
                    action = status = file = ""
                    parts = [p.strip() for p in rest.split('|')]
                    for part in parts:
                        if part.startswith("Action:"):
                            action = part.replace("Action:", "").strip()
                        elif part.startswith("Status:"):
                            status = part.replace("Status:", "").strip()
                        elif part.startswith("File:"):
                            file = part.replace("File:", "").strip()

                    logs.append({
                        "timestamp": timestamp,
                        "level": level,
                        "user": user,
                        "action": action,
                        "status": status,
                        "file": file
                    })

                except:
                    pass  

    return render_template("log_security.html", logs=logs)

