from .auth_routes import auth_bp
from .crypto_routes import crypto_bp
from .utils_routes import utils_bp

def register_all_routes(app):
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(crypto_bp, url_prefix='/crypto')
    app.register_blueprint(utils_bp, url_prefix='/utils')
