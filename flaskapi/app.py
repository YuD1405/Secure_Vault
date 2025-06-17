from flask import Flask
from flask_cors import CORS
from flask_mysqldb import MySQL
import os

mysql = MySQL()


def create_app():
    app = Flask(__name__)
    CORS(app)

    # Load biến môi trường nếu có
    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
    app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'secure_vault')


    mysql.init_app(app)

    from flaskapi.routes.main_routes import main_routes
    app.register_blueprint(main_routes)

    return app
