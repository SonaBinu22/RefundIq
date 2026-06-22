import os
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

_DEFAULT_SECRET = None
_DEFAULT_JWT    = None


class Config:
    SECRET_KEY     = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

    if not SECRET_KEY or not JWT_SECRET_KEY:
        raise RuntimeError(
            '\n🚫 SECRET_KEY and JWT_SECRET_KEY must be set as environment variables.\n'
            '   Copy .env.example to .env and fill in real values.'
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
