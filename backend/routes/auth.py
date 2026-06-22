import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

auth_bp = Blueprint('auth', __name__, url_prefix='/api')
limiter = Limiter(key_func=get_remote_address)

MAX_FAILED   = 5
LOCKOUT_MINS = 15
PW_HISTORY   = 5   # remember last N passwords


@auth_bp.route('/register', methods=['POST'])
@limiter.limit('10 per hour')
def register():
    from backend.models import db, User
    from backend.services.audit_service import log as audit_log

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    for f in ['name', 'email', 'password']:
        if not data.get(f):
            return jsonify({'error': f'{f} is required'}), 400
    if len(data['password']) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if User.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'error': 'Email already registered'}), 409

    hashed = generate_password_hash(data['password']).decode('utf-8')
    user = User(
        name=data['name'],
        email=data['email'].lower(),
        password=hashed,
        phone=data.get('phone', ''),
        role='customer',
        password_history=json.dumps([hashed])
    )
    db.session.add(user)
    db.session.commit()

    audit_log('register', 'User', user.user_id, new_value=user.email)
    token = create_access_token(identity=str(user.user_id))
    return jsonify({'message': 'Registration successful', 'token': token, 'user': user.to_dict()}), 201


@auth_bp.route('/login', methods=['POST'])
@limiter.limit('5 per minute; 20 per hour')
def login():
    from backend.models import db, User
    from backend.services.audit_service import log as audit_log
    from backend.services.email_service import send_account_locked

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    user = User.query.filter_by(email=data.get('email', '').lower()).first()
    dummy = '$2b$12$KIXxyzDUMMYHASHtopreventuserenum'
    pwd   = data.get('password', '')

    if not user:
        check_password_hash(dummy, pwd)
        return jsonify({'error': 'Invalid email or password'}), 401

    if user.is_locked():
        remaining = int((user.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
        return jsonify({'error': f'Account locked. Try again in {remaining} minute(s).'}), 423

    if not check_password_hash(user.password, pwd):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= MAX_FAILED:
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINS)
            user.failed_login_attempts = 0
            db.session.commit()
            audit_log('account_locked', 'User', user.user_id, user_id=user.user_id)
            try:
                send_account_locked(user.email, user.name, LOCKOUT_MINS)
            except Exception:
                pass
            return jsonify({'error': f'Account locked for {LOCKOUT_MINS} minutes after too many failed attempts.'}), 423
        db.session.commit()
        return jsonify({'error': 'Invalid email or password'}), 401

    # Successful login
    user.failed_login_attempts = 0
    user.locked_until           = None
    user.last_login             = datetime.utcnow()
    db.session.commit()

    audit_log('login', 'User', user.user_id, user_id=user.user_id)
    token = create_access_token(identity=str(user.user_id))
    return jsonify({'message': 'Login successful', 'token': token, 'user': user.to_dict()})


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    from backend.models import User
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()})


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@limiter.limit('5 per hour')
def change_password():
    from backend.models import db, User
    from backend.services.audit_service import log as audit_log
    from backend.services.email_service import send_password_changed

    uid  = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data    = request.get_json() or {}
    current = data.get('current_password', '')
    new_pwd = data.get('new_password', '')

    if not current or not new_pwd:
        return jsonify({'error': 'current_password and new_password are required'}), 400
    if len(new_pwd) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if not check_password_hash(user.password, current):
        return jsonify({'error': 'Current password is incorrect'}), 401
    if current == new_pwd:
        return jsonify({'error': 'New password must differ from current'}), 400

    # Check password history
    history = json.loads(user.password_history or '[]')
    for old_hash in history:
        if check_password_hash(old_hash, new_pwd):
            return jsonify({'error': 'Password was recently used. Choose a different one.'}), 400

    new_hash = generate_password_hash(new_pwd).decode('utf-8')
    history  = ([new_hash] + history)[:PW_HISTORY]
    user.password          = new_hash
    user.password_history  = json.dumps(history)
    db.session.commit()

    audit_log('password_changed', 'User', uid, user_id=uid)
    try:
        send_password_changed(user.email, user.name)
    except Exception:
        pass
    return jsonify({'message': 'Password changed successfully'})
