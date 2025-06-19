from flask import Blueprint, request, jsonify

crypto_bp = Blueprint('crypto', __name__)

@crypto_bp.route("/encrypt_file")
def encrypt_file():
    return "Encrypt"

@crypto_bp.route("/decrypt_file")
def decrypt_file():
    return "decrypt"

@crypto_bp.route("/manage_keys")
def manage_keys():
    return "manage_keys"