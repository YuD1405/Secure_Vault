from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from modules.crypto.key_management import get_all_key_strings
from modules.crypto.key_generator import create_new_key

crypto_bp = Blueprint('crypto', __name__)

# Requirement 3 – RSA key managements
@crypto_bp.route("/render_manage_keys", methods=['GET'])
def render_manage_keys():
    return render_template("manage_keys.html")

# Hàm để lấy toàn bộ keys (pri + pub + exp) của người dùng => bảng toàn bộ key người dùng trên fe
@crypto_bp.route("/manage_keys", methods=['GET'])
def manage_keys():
    # --- Bắt đầu khối kiểm tra session ---
    if 'user_id' not in session:
        flash("Bạn cần phải đăng nhập để truy cập trang này.", "error")
        return redirect(url_for('auth.login'))
    # --- Kết thúc khối kiểm tra session ---
    
    email = session["email"] # Lấy email trực tiếp từ session

    all_keys = get_all_key_strings(email)
    contacts = get_all_contacts(email)

    return render_template("manage_keys.html", all_keys=all_keys, contacts=contacts)

# Hàm để tạo key mới và deactivate các key cũ => nút tạo key mới trên fe
@crypto_bp.route("/regenerate_key", methods=["GET", "POST"])
def regenerate_key():
    if 'user_id' not in session:
        flash("Phiên làm việc đã hết hạn.", "error")
        return redirect(url_for('auth.login'))
        
    email = session["email"]
    hashed_passphrase_hex = session.get('hashed_passphrase_hex')
    if not hashed_passphrase_hex:
        flash("Lỗi phiên làm việc, không tìm thấy thông tin xác thực.", "error")
        session.clear()
        return redirect(url_for('auth.login'))
    
    try:
        aes_key = key_utils.derive_aes_key_from_hash(hashed_passphrase_hex)
    except ValueError:
        flash("Lỗi phiên làm việc.", "error")
        session.clear()
        return redirect(url_for('auth.login'))
    # --- Kết thúc khối kiểm tra và chuẩn bị dữ liệu ---

    success, message = key_utils.force_create_new_key(email, aes_key)
    
    if success:
        flash(message, "success")
    else:
        flash(message, "error")
        
    return redirect(url_for('crypto.manage_keys'))

# Requirement 6 – Encrypt
@crypto_bp.route('/render_encrypt', methods=['GET'])
def render_encrypt():
    return render_template('encrypt.html')

# Hàm gọi module encrypt , js sẽ truyền xuống 1 file và pubkey của người nhận => trả về 1 file đã mã để fe xử lí download
@crypto_bp.route("/encrypt_file", methods=['POST'])
def encrypt_file():
     # --- Bắt đầu khối kiểm tra session ---
    if 'user_id' not in session:
        return {"error": "Phiên làm việc đã hết hạn"}, 401 # Trả về lỗi cho JS
    # --- Kết thúc khối kiểm tra session ---

    sender_email = session["email"]
    recipient_email = request.form.get('recipient_email')
    file = request.files.get('file_to_encrypt')
    output_option = request.form.get('output_option', 'merge')

    if not file or not recipient_email or file.filename == '':
        flash("Vui lòng chọn file và nhập email người nhận.", "error")
        return redirect(url_for('crypto.manage_keys'))

    output_dir = key_utils.get_user_dir(sender_email) / "encrypted_files"
    output_dir.mkdir(exist_ok=True)

    success, message = key_utils.encrypt_file_for_recipient(
        sender_email=sender_email,
        recipient_email=recipient_email,
        file_stream=file.stream,
        original_filename=file.filename,
        output_dir=output_dir,
        merge_output=(output_option == 'merge')
    )

    if success:
        flash(message, "success")
    else:
        flash(message, "error")

    return redirect(url_for('crypto.manage_keys'))

# Requirement 7 – Decrypt
@crypto_bp.route('/render_decrypt', methods=['GET'])
def render_decrypt():
     # --- Bắt đầu khối kiểm tra và chuẩn bị dữ liệu ---
    if 'user_id' not in session:
        return {"error": "Phiên làm việc đã hết hạn"}, 401

    recipient_email = session["email"]
    hashed_passphrase_hex = session.get('hashed_passphrase_hex')
    if not hashed_passphrase_hex:
        flash("Lỗi phiên làm việc.", "error")
        return redirect(url_for('auth.login'))
        
    try:
        aes_key = key_utils.derive_aes_key_from_hash(hashed_passphrase_hex)
    except ValueError:
        flash("Lỗi phiên làm việc.", "error")
        return redirect(url_for('auth.login'))
    # --- Kết thúc khối kiểm tra và chuẩn bị dữ liệu ---

    enc_file = request.files.get('enc_file')
    key_file = request.files.get('key_file')

    if not enc_file or enc_file.filename == '':
        flash("Vui lòng chọn file .enc để giải mã.", "error")
        return redirect(url_for('crypto.manage_keys'))

    key_file_stream = key_file.stream if key_file and key_file.filename != '' else None
    
    success, message, metadata, decrypted_content = key_utils.decrypt_file_from_sender(
        recipient_email=recipient_email,
        recipient_aes_key=aes_key,
        enc_file_stream=enc_file.stream,
        key_file_stream=key_file_stream
    )

    if success:
        original_filename = metadata.get('original_filename', 'decrypted_file.dat')
        
        response = make_response(decrypted_content)
        response.headers.set('Content-Type', 'application/octet-stream')
        response.headers.set('Content-Disposition', 'attachment', filename=original_filename)
        
        flash(f"Giải mã thành công file '{original_filename}'!", "success")
        return response
    else:
        flash(f"Giải mã thất bại: {message}", "error")
        return redirect(url_for('crypto.manage_keys'))

# Hàm gọi module decrypt , js sẽ truyền xuống 1 file > trả về 1 file đã giải mã để fe xử lí download
@crypto_bp.route("/decrypt_file", methods=['POST']) 
def decrypt_file():
    return "decrypt"
