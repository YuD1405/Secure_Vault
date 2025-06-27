from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, make_response
from modules.crypto.key_management import get_all_key_strings,check_and_manage_own_keys
from modules.crypto.key_generator import create_new_key
from modules.crypto.encrypt import encrypt_file_for_recipient, decrypt_file_from_sender
from modules.crypto.key_extensions import get_user_dir, Path
from modules.utils.qr_code import get_all_contacts
from modules.auth.logic import check_correct_pw
import io
import zipfile
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
    check_and_manage_own_keys(email)
    all_keys = get_all_key_strings(email)

    return render_template("manage_keys.html", all_keys=all_keys)

# Hàm để tạo key mới và deactivate các key cũ => nút tạo key mới trên fe
@crypto_bp.route("/regenerate_key", methods=["GET", "POST"])
def regenerate_key():
    if 'user_id' not in session:
        flash("Phiên làm việc đã hết hạn.", "error")
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        email = session["email"]
        passphrase = session.get("passphrase")
        if not passphrase:
            flash("Lỗi phiên làm việc, không tìm thấy thông tin xác thực.", "error")
            session.clear()
            return redirect(url_for('auth.login'))
        
        try:
            aes_key = passphrase #
        except ValueError:
            flash("Lỗi phiên làm việc.", "error")
            session.clear()
            return redirect(url_for('auth.login'))
        # --- Kết thúc khối kiểm tra và chuẩn bị dữ liệu ---

        success = create_new_key(email, aes_key)
        
        if success:
            flash("success")
        else:
            flash("error")
            
    return redirect(url_for('crypto.manage_keys'))

# Requirement 6 – Encrypt
@crypto_bp.route('/render_encrypt', methods=['GET'])
def render_encrypt():
    return render_template('encrypt.html')





# Hàm gọi module encrypt , js sẽ truyền xuống 1 file và pubkey của người nhận => trả về 1 file đã mã để fe xử lí download
@crypto_bp.route('/encrypt-server-file', methods=['POST'])
def encrypt_file():
    """
    Nhận một file được upload, mã hoá cho người nhận, và trả về file
    kết quả (.enc hoặc .zip) để người dùng tải xuống.
    """
    # --- Bắt đầu khối kiểm tra session ---
    if 'user_id' not in session:
        # Trả về lỗi JSON nếu request này được gọi bằng AJAX/JS
        return {"error": "Phiên làm việc đã hết hạn"}, 401
    # --- Kết thúc khối kiểm tra session ---

    # 1. Lấy thông tin từ request POST và file upload
    sender_email = session["email"]
    recipient_email = request.form.get('recipient_email')
    file_to_encrypt = request.files.get('file_to_encrypt') # <-- Lấy file upload
    output_option = request.form.get('output_option', 'merge')

    # 2. Kiểm tra đầu vào
    if not file_to_encrypt or not recipient_email or file_to_encrypt.filename == '':
        flash("Vui lòng chọn file và nhập email người nhận.", "error")
        return redirect(url_for('crypto.manage_keys')) # Hoặc trang mã hoá

    # 3. Chuẩn bị thư mục output và các tham số
    output_dir = get_user_dir(sender_email) / "encrypted_outputs"
    output_dir.mkdir(exist_ok=True)
    merge_output = (output_option == 'merge')

    # 4. Gọi hàm mã hoá
    success, message = encrypt_file_for_recipient(
        sender_email=sender_email,
        recipient_email=recipient_email,
        file_stream=file_to_encrypt.stream, # <-- Dùng stream từ file upload
        original_filename=file_to_encrypt.filename,
        output_dir=output_dir,
        merge_output=merge_output
    )

    if not success:
        flash(f"Mã hoá thất bại: {message}", "error")
        return redirect(url_for('crypto.manage_keys'))

    # 5. Xử lý kết quả và gửi file về cho người dùng
    try:
        original_filename = file_to_encrypt.filename
        original_filename_base = Path(original_filename).stem

        if merge_output:
            # Trường hợp gộp file: Gửi trực tiếp file .enc
            encrypted_file_path = output_dir / f"{original_filename}.enc"
            return send_file(
                encrypted_file_path,
                as_attachment=True
            )
        else:
            # Trường hợp tách file: Nén thành ZIP và gửi về
            enc_file_path = output_dir / f"{original_filename}.enc"
            key_file_path = output_dir / f"{original_filename}.key"

            if not (enc_file_path.exists() and key_file_path.exists()):
                 raise FileNotFoundError("Không thể tạo đầy đủ các file mã hoá.")

            # Nén 2 file vào một file ZIP trong bộ nhớ
            memory_file = io.BytesIO()
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(enc_file_path, arcname=enc_file_path.name)
                zf.write(key_file_path, arcname=key_file_path.name)
            memory_file.seek(0)

            # Gửi file ZIP về
            return send_file(
                memory_file,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f"{original_filename_base}_encrypted.zip"
            )
    except Exception as e:
        flash(f"Đã xảy ra lỗi khi chuẩn bị file để tải xuống: {e}", "error")
        return redirect(url_for('crypto.manage_keys'))




# Requirement 7 – Decrypt
@crypto_bp.route('/render_decrypt', methods=['GET'])
def render_decrypt():
    return render_template('decrypt.html')


# Hàm gọi module decrypt , js sẽ truyền xuống 1 file > trả về 1 file đã giải mã để fe xử lí download
@crypto_bp.route("/decrypt-file", methods=['POST'])
def decrypt_file():
    # --- Bắt đầu khối kiểm tra và chuẩn bị dữ liệu ---
    if 'user_id' not in session:
        return {"error": "Phiên làm việc đã hết hạn"}, 401

    recipient_email = session["email"]
    passphrase = session.get('passphrase')
    if not passphrase:
        flash("Lỗi phiên làm việc.", "error")
        return redirect(url_for('auth.login'))
        
    try:  
        aes_key = passphrase
    except ValueError:
        flash("Lỗi phiên làm việc.", "error")
        return redirect(url_for('auth.login'))
    # --- Kết thúc khối kiểm tra và chuẩn bị dữ liệu ---

    # 1. Lấy file upload duy nhất từ request
    uploaded_file = request.files.get('file_to_decrypt')

    if not uploaded_file or uploaded_file.filename == '':
        flash("Vui lòng chọn một file (.enc hoặc .zip) để giải mã.", "error")
        return redirect(url_for('crypto.manage_keys'))

    filename = uploaded_file.filename
    enc_file_stream = None
    key_file_stream = None

    try:
        # 2. Kiểm tra loại file và trích xuất các stream cần thiết
        if filename.lower().endswith('.zip'):
            print("Phát hiện file ZIP, đang giải nén trong bộ nhớ...")
            # Mở file ZIP trong bộ nhớ
            with zipfile.ZipFile(uploaded_file.stream, 'r') as zf:
                # Tìm file .enc và .key bên trong ZIP
                for name in zf.namelist():
                    if name.lower().endswith('.enc'):
                        enc_file_stream = io.BytesIO(zf.read(name))
                    elif name.lower().endswith('.key'):
                        key_file_stream = io.BytesIO(zf.read(name))
            
            if not enc_file_stream or not key_file_stream:
                flash("File ZIP không chứa đủ file .enc và .key cần thiết.", "error")
                return redirect(url_for('crypto.manage_keys'))

        elif filename.lower().endswith('.enc'):
            print("Phát hiện file .enc gộp.")
            enc_file_stream = uploaded_file.stream
            # key_file_stream sẽ là None, đúng cho trường hợp file gộp
        else:
            flash("Định dạng file không được hỗ trợ. Vui lòng upload file .enc hoặc .zip.", "error")
            return redirect(url_for('crypto.manage_keys'))

        # 3. Gọi hàm giải mã logic
        success, message, metadata, decrypted_content = decrypt_file_from_sender(
            recipient_email=recipient_email,
            recipient_aes_key=aes_key,
            enc_file_stream=enc_file_stream,
            key_file_stream=key_file_stream
        )

        # 4. Xử lý kết quả và gửi file đã giải mã về
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

    except zipfile.BadZipFile:
        flash("File ZIP bị lỗi hoặc không hợp lệ.", "error")
        return redirect(url_for('crypto.manage_keys'))
    except Exception as e:
        flash(f"Đã xảy ra lỗi không xác định trong quá trình giải mã: {e}", "error")
        return redirect(url_for('crypto.manage_keys'))
    
