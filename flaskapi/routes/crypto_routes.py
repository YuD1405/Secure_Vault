from flask import Blueprint, render_template, request, redirect, url_for, session, flash

crypto_bp = Blueprint('crypto', __name__)

# Requirement 3 – RSA key managements
@crypto_bp.route("/render_manage_keys")
def render_manage_keys():
    return render_template("manage_keys.html")

# Requirement 6 – Encrypt
@crypto_bp.route('/render_encrypt', methods=['GET'])
def render_encrypt():
    return render_template('encrypt.html')

@crypto_bp.route("/encrypt_file")
def encrypt_file():
    return "Encrypt"

# Requirement 7 – Decrypt
@crypto_bp.route('/render_decrypt', methods=['GET'])
def render_decrypt():
    return render_template('decrypt.html')

@crypto_bp.route("/decrypt_file")
def decrypt_file():
    return "decrypt"
