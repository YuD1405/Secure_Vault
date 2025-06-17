from flask import Flask
from flask_cors import CORS
from flaskapi.routes import register_all_routes

def create_app():
    app = Flask(__name__)
    CORS(app)
    register_all_routes(app)  
    return app

