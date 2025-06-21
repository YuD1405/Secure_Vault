from flask import Blueprint, render_template, request, redirect, url_for, session, flash

crypto_bp = Blueprint('crypto', __name__)

@crypto_bp.route("/encrypt_file")
def encrypt_file():
    return "Encrypt"

@crypto_bp.route("/decrypt_file")
def decrypt_file():
    return "decrypt"

@crypto_bp.route("/manage_keys")
def manage_keys():
    return render_template("manage_keys.html")