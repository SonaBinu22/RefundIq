import os
import warnings
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, '..', 'database')
os.makedirs(DB_DIR, exist_ok=True)

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, '..', '.env'))
except ImportError:
    pass

_DEFAULT_SECRET = 'refundiq-secret-key-2024'
_DEFAULT_JWT    = 'refundiq-jwt-secret-2024'


class Config:
    SECRET_KEY     = os.environ.get('SECRET_KEY', _DEFAULT_SECRET)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', _DEFAULT_JWT)

    # Warn loudly if running with default secrets
    if SECRET_KEY == _DEFAULT_SECRET or JWT_SECRET_KEY == _DEFAULT_JWT:
        warnings.warn(
            '\n⚠️  SECURITY WARNING: Using default secret keys! '
            'Set SECRET_KEY and JWT_SECRET_KEY environment variables '
            'or add them to a .env file before deploying.',
            stacklevel=2
        )

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.abspath(os.path.join(DB_DIR, 'refundiq.db'))}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES       = timedelta(hours=12)
    UPLOAD_FOLDER      = os.path.join(BASE_DIR, '..', 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'mp4', 'pdf'}
