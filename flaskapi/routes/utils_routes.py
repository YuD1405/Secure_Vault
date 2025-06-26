from flask import Blueprint, request, render_template, jsonify, send_file, session, flash, redirect, url_for
from modules.utils.qr_code import generate_public_info_qr, process_qr_code_and_add_contact, get_user_dir
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

# Requirement 4 – QR
@utils_bp.route('/generate_qr', methods=['GET'])
def generate_qr():
    """
    Tạo một mã QR từ email được cung cấp qua query parameter.
    Ví dụ: /utils/generate_qr?email=user@example.com
    """
    # 1. Lấy email từ query parameter của URL
    email = request.args.get('email')

    # 2. Kiểm tra xem email có được cung cấp không
    if not email:
        # Nếu bạn có trang lỗi, có thể render nó.
        # Hoặc trả về lỗi JSON.
        return "Lỗi: Vui lòng cung cấp một địa chỉ email trong URL (ví dụ: ?email=user@example.com)", 400

    try:
        # 3. Xác định đường dẫn output cho file QR
        # Lưu vào một thư mục tạm thời hoặc thư mục của người dùng
        user_dir = get_user_dir(email)
        qr_output_path = user_dir / f"{email.replace('@', '_at_')}_qr.png"

        # 4. Gọi hàm logic để tạo file ảnh QR
        # Giả sử hàm generate_qr_image_file trả về True/False
        success, message = generate_public_info_qr(email=email, output_path=qr_output_path)

        if not success:
            # Nếu hàm tạo QR thất bại (ví dụ không tìm thấy public key)
            print(f"Lỗi khi tạo QR", message)
            # Có thể trả về một ảnh placeholder "lỗi"
            return f"Không thể tạo QR code", 500

        # 5. Gửi file ảnh vừa tạo về cho trình duyệt
        return send_file(
            qr_output_path,
            mimetype='image/png'
        )

    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tạo QR code cho {email}: {e}")
        return "Đã xảy ra lỗi không xác định trên server.", 500

@utils_bp.route('/decode_qr', methods=['POST'])
def decode_qr():
    """
    Nhận một file ảnh QR, giải mã và thêm thông tin vào danh bạ
    của người dùng đang đăng nhập (lấy từ session).
    """
    # 1. Bắt đầu khối kiểm tra session
    # Kiểm tra xem người dùng đã đăng nhập hoàn toàn chưa
    if 'user_id' not in session:
        flash("Bạn cần phải đăng nhập để thực hiện hành động này.", "error")
        # Nếu đây là một request từ JS (AJAX), bạn có thể muốn trả về JSON
        # return jsonify({"error": "Unauthorized"}), 401
        return redirect(url_for('auth.login'))

    # Lấy email trực tiếp từ session
    current_user_email = session.get("email")

    if not current_user_email:
        # Trường hợp hi hữu session có user_id nhưng không có email
        flash("Lỗi phiên làm việc, vui lòng đăng nhập lại.", "error")
        session.clear()
        return redirect(url_for('auth.login'))
    # --- Kết thúc khối kiểm tra session ---

    # 2. Kiểm tra file upload
    if 'qr_code_file' not in request.files:
        flash("Không có file nào được chọn.", "error")
        return redirect(url_for('crypto.manage_keys'))

    file = request.files['qr_code_file']
    if file.filename == '':
        flash("Chưa chọn file nào.", "error")
        return redirect(url_for('crypto.manage_keys'))

    # 3. Gọi hàm xử lý logic
    if file:
        success, message = process_qr_code_and_add_contact(
            current_user_email=current_user_email, # <-- Sử dụng biến lấy từ session
            qr_image_stream=file.stream
        )
        
        # 4. Flash thông báo kết quả
        if success:
            flash(message, "success")
        else:
            flash(message, "error")

    # 5. Chuyển hướng người dùng trở lại
    return redirect(url_for('crypto.manage_keys'))

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

