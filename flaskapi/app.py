from flask import Flask
from flask_cors import CORS
import os
from flaskapi.routes import register_all_routes 
from flaskapi.extensions import mysql 

def create_app():
    template_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "templates")
    static_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "static")
    app = Flask(__name__, template_folder=template_path, static_folder=static_path)
    CORS(app)

    # Load biến môi trường nếu có
    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
    app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'secure_vault')


    mysql.init_app(app)
    register_all_routes(app)

    return app