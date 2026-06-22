import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR   = os.path.join(BASE_DIR, '..', 'database')
os.makedirs(DB_DIR, exist_ok=True)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, '..', '.env'))
except ImportError:
    pass


class Config:
    # ── Secrets ──────────────────────────────────────────────
    SECRET_KEY     = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

    if not SECRET_KEY or not JWT_SECRET_KEY:
        import warnings
        warnings.warn(
            '⚠️  SECRET_KEY and JWT_SECRET_KEY not set. '
            'Copy .env.example to .env and set real values.',
            stacklevel=2
        )
        SECRET_KEY     = SECRET_KEY or 'dev-secret-key-change-me'
        JWT_SECRET_KEY = JWT_SECRET_KEY or 'dev-jwt-key-change-me'

    # ── Database ──────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.abspath(os.path.join(DB_DIR, 'refundiq.db'))}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── JWT ───────────────────────────────────────────────────
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)

    # ── Uploads ───────────────────────────────────────────────
    UPLOAD_FOLDER      = os.path.join(BASE_DIR, '..', 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'mp4', 'pdf'}

    # ── Email (optional) ─────────────────────────────────────
    MAIL_SERVER   = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@refundiq.com')

    # ── CORS ──────────────────────────────────────────────────
    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*')

    # ── Gemini AI (optional) ──────────────────────────────────
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
