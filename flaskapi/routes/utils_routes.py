from flask import Blueprint, request, render_template, jsonify
from modules.utils.digital_signing import digital_sign_file
from modules.utils.verify_digital_signature import verify_signature
from modules.utils.logger import log_user_action
import os

utils_bp = Blueprint('utils', __name__)


# Render Page
@utils_bp.route('/digital_signature', methods=['GET'])
def digital_signature():
    return render_template('digital_signature.html')  

# Route 8 – File Signing
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

# Route 9 – Verify Digital Signature
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

@utils_bp.route("/log_security")
def log_security():
    return "Logging"
