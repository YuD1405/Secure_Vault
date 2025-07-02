from flask import Flask, session
from flask_cors import CORS
import os
from flaskapi.routes import register_all_routes 
from flaskapi.extensions import mysql 
from dotenv import load_dotenv

def create_app():
    load_dotenv()
    
    template_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "templates")
    static_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "static")
    app = Flask(__name__, template_folder=template_path, static_folder=static_path)
    app.secret_key = os.getenv("FLASK_SECRET_KEY")
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = True  # Chỉ hoạt động qua HTTPS
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
    CORS(app)

    # Load biến môi trường nếu có
    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD') 
    app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
    app.config['MYSQL_CURSORCLASS'] = os.getenv('MYSQL_CURSORCLASS')

    mysql.init_app(app)
    register_all_routes(app)

    return app