from flask import Blueprint, request, render_template, current_app, jsonify
from modules.utils.digital_signing import digital_sign_file
from modules.utils.verify_digital_signature import verify_signature
import os

utils_bp = Blueprint('utils', __name__)

# Render templates
@utils_bp.route('/digital_signature', methods=['GET'])
def digital_signature():
    return render_template('digital_signature.html')  

# 8 - Signing
@utils_bp.route('/sign_file', methods=['POST'])
def signing_file_route():
    if 'file' not in request.files:
        return jsonify({'error': 'Không có file nào'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Tên file trống'}), 400

    private_key_path = 'data/keys/private.pem'
    if not os.path.exists(private_key_path):
        return jsonify({'error': 'Không tìm thấy private key!'}), 500

    # Ký
    signature = digital_sign_file(file, private_key_path)

    sig_folder = "data/signature"
    os.makedirs(sig_folder, exist_ok=True)
    sig_path = os.path.join(sig_folder, file.filename + ".sig")
    
    # Lưu chữ ký vào file
    with open(sig_path, 'wb') as sig_file:
        sig_file.write(signature)

    return jsonify({'message': '✅ Đã ký số thành công!',})

# 9 - Verify Signature
@utils_bp.route('/verify_signature', methods=['POST'])
def verify_signature_route():
    if 'file' not in request.files or 'signature' not in request.files:
        return jsonify({"success": False, "message": "No file or signature provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Tên file trống'}), 400
    
    signature = request.files['signature'].read()  
    
    public_key_path = request.form.get('public_key_path', 'data/keys/public.pem')

    if not os.path.exists(public_key_path):
        return jsonify({"success": False, "message": "Public key không tồn tại"}), 400

    # Xác minh chữ ký
    is_valid = verify_signature(file, signature, public_key_path)
    
    if is_valid:
        return jsonify({"success": True, "message": "Signature is valid."}), 200
    else:
        return jsonify({"success": False, "message": "Signature is invalid."}), 400
    
@utils_bp.route("/generate_qr")
def generate_qr():
    return "Gen Qr"

@utils_bp.route("/log_security")
def log_security():
    return "Logging"