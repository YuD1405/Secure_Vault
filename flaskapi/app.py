from flask import Flask
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
    CORS(app)

    # Load biến môi trường nếu có
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'DangDuy06072004!' # Replace with your actual password
    app.config['MYSQL_DB'] = 'secure_vault'
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

    mysql.init_app(app)
    register_all_routes(app)

    return app