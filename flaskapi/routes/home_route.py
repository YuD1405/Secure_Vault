# flaskapi/routes/home_route.py
from flask import Blueprint, redirect, url_for, session

# Tạo Blueprint cho route 'home'
home = Blueprint('home', __name__)

@home.route("/")
def home_page():
    if session.get("user_id"):
        return redirect(url_for("auth.dashboard")) 
    return redirect(url_for("auth.login")) 
