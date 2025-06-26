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
    
    return "manage key"

# Hàm để tạo key mới và deactivate các key cũ => nút tạo key mới trên fe
@crypto_bp.route("/regenerate_key", methods=["GET", "POST"])
def regenerate_key():
   
    return "regen key"

# Requirement 6 – Encrypt
@crypto_bp.route('/render_encrypt', methods=['GET'])
def render_encrypt():
    return render_template('encrypt.html')

# Hàm gọi module encrypt , js sẽ truyền xuống 1 file và pubkey của người nhận => trả về 1 file đã mã để fe xử lí download
@crypto_bp.route("/encrypt_file", methods=['POST'])
def encrypt_file():
    return "Encrypt"

# Requirement 7 – Decrypt
@crypto_bp.route('/render_decrypt', methods=['GET'])
def render_decrypt():
    return render_template('decrypt.html')

# Hàm gọi module decrypt , js sẽ truyền xuống 1 file > trả về 1 file đã giải mã để fe xử lí download
@crypto_bp.route("/decrypt_file", methods=['POST']) 
def decrypt_file():
    return "decrypt"
