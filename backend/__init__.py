import os


def create_app():
    from flask import Flask
    from flask_jwt_extended import JWTManager
    from flask_bcrypt import Bcrypt
    from flask_cors import CORS
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    from flasgger import Swagger

    from backend.models.db import db
    from backend.config import Config
    from backend.routes.auth import limiter
    from backend.realtime import init_socketio

    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)

    # Extensions
    db.init_app(app)
    Bcrypt(app)
    JWTManager(app)
    CORS(app, resources={r'/api/*': {'origins': app.config.get('ALLOWED_ORIGINS', '*')}})
    limiter.init_app(app)
    init_socketio(app)

    # Swagger docs
    Swagger(app, template={
        'info': {'title': 'RefundIQ+ API', 'version': '2.0',
                 'description': 'Enterprise AI-Powered Refund Fraud Detection Platform'},
        'securityDefinitions': {
            'Bearer': {'type': 'apiKey', 'name': 'Authorization', 'in': 'header'}
        }
    })

    # Email
    from backend.services.email_service import init_mail
    init_mail(app)

    # Blueprints
    from backend.routes.pages   import pages_bp
    from backend.routes.auth    import auth_bp
    from backend.routes.refund  import refund_bp
    from backend.routes.admin   import admin_bp
    from backend.routes.analytics import analytics_bp
    from backend.routes.chat    import chat_bp
    from backend.routes.reports import reports_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(refund_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(reports_bp)

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options']    = 'nosniff'
        response.headers['X-Frame-Options']           = 'DENY'
        response.headers['X-XSS-Protection']          = '1; mode=block'
        response.headers['Referrer-Policy']           = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy']        = 'geolocation=(), microphone=()'
        return response

    with app.app_context():
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        db.create_all()
        _seed_admin()

    return app


def _seed_admin():
    import json
    from flask_bcrypt import generate_password_hash
    from backend.models import db, User
    if not User.query.filter_by(role='admin').first():
        hashed = generate_password_hash('admin123').decode('utf-8')
        admin = User(
            name='Admin',
            email='admin@refundiq.com',
            password=hashed,
            role='admin',
            password_history=json.dumps([hashed])
        )
        db.session.add(admin)
        db.session.commit()
        print('Default admin created: admin@refundiq.com / admin123')

    if not User.query.filter_by(role='superadmin').first():
        hashed = generate_password_hash('superadmin123').decode('utf-8')
        sa = User(
            name='Super Admin',
            email='superadmin@refundiq.com',
            password=hashed,
            role='superadmin',
            password_history=json.dumps([hashed])
        )
        db.session.add(sa)
        db.session.commit()
        print('Super admin created: superadmin@refundiq.com / superadmin123')
