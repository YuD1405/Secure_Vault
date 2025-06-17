from flask import Blueprint, request, jsonify
from modules.auth.login import login_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    ok, msg = login_user(data['email'], data['passphrase'])
    return jsonify({"success": ok, "message": msg})
