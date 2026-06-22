from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

# Limiter instance — attached to app in create_app
limiter = Limiter(key_func=get_remote_address)


@auth_bp.route('/register', methods=['POST'])
@limiter.limit('10 per hour')
def register():
    from backend.models import db, User
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    for field in ['name', 'email', 'password']:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    if len(data['password']) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    if User.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'error': 'Email already registered'}), 409

    user = User(
        name=data['name'],
        email=data['email'].lower(),
        password=generate_password_hash(data['password']).decode('utf-8'),
        phone=data.get('phone', ''),
        role='customer'
    )
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.user_id))
    return jsonify({'message': 'Registration successful', 'token': token, 'user': user.to_dict()}), 201


@auth_bp.route('/login', methods=['POST'])
@limiter.limit('5 per minute; 20 per hour')
def login():
    from backend.models import User
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    user = User.query.filter_by(email=data.get('email', '').lower()).first()
    # Constant-time check even on missing user to prevent user enumeration
    dummy_hash = '$2b$12$KIXxyzDUMMYHASHtopreventuserenum'
    pwd = data.get('password', '')
    if not user:
        check_password_hash(dummy_hash, pwd)  # prevent timing attack
        return jsonify({'error': 'Invalid email or password'}), 401
    if not check_password_hash(user.password, pwd):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = create_access_token(identity=str(user.user_id))
    return jsonify({'message': 'Login successful', 'token': token, 'user': user.to_dict()}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    from backend.models import User
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@limiter.limit('5 per hour')
def change_password():
    from backend.models import db, User
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}
    current = data.get('current_password', '')
    new_pwd  = data.get('new_password', '')

    if not current or not new_pwd:
        return jsonify({'error': 'current_password and new_password are required'}), 400
    if len(new_pwd) < 8:
        return jsonify({'error': 'New password must be at least 8 characters'}), 400
    if not check_password_hash(user.password, current):
        return jsonify({'error': 'Current password is incorrect'}), 401
    if current == new_pwd:
        return jsonify({'error': 'New password must differ from current password'}), 400

    user.password = generate_password_hash(new_pwd).decode('utf-8')
    db.session.commit()
    return jsonify({'message': 'Password changed successfully'}), 200
