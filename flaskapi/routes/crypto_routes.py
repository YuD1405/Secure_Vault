from flask import Blueprint, render_template, request, redirect, url_for, session, flash

crypto_bp = Blueprint('crypto', __name__)

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

@crypto_bp.route("/manage_keys")
def manage_keys():
    return render_template("manage_keys.html")