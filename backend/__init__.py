import os


def create_app():
    from flask import Flask
    from flask_jwt_extended import JWTManager
    from flask_bcrypt import Bcrypt
    from flask_cors import CORS
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    from backend.models.db import db
    from backend.config import Config
    from backend.routes.auth import limiter

    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)

    db.init_app(app)
    Bcrypt(app)
    JWTManager(app)
    CORS(app)
    limiter.init_app(app)

    from backend.routes.auth import auth_bp
    from backend.routes.refund import refund_bp
    from backend.routes.admin import admin_bp
    from backend.routes.pages import pages_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(refund_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        db.create_all()
        _seed_admin()

    return app


def _seed_admin():
    """Create a default admin account if none exists."""
    from flask_bcrypt import generate_password_hash
    from backend.models import db, User
    if not User.query.filter_by(role='admin').first():
        admin = User(
            name='Admin',
            email='admin@refundiq.com',
            password=generate_password_hash('admin123').decode('utf-8'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print('Default admin created: admin@refundiq.com / admin123')
