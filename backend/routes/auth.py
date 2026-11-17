from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from models.models import db, User
from helpers import err, role_required, current_user_id

auth_bp = Blueprint('auth', __name__, url_prefix='/api')


@auth_bp.route('/register', methods=['POST'])
def register():
    # only students can register
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    name = (data.get('name') or '').strip()
    password = data.get('password') or ''

    if not username or not email or not name or not password:
        return err('Name, username, email and password are required')
    if '@' not in email:
        return err('Enter a valid email')
    if len(password) < 6:
        return err('Password must have at least 6 characters')
    if User.query.filter_by(username=username).first():
        return err('Username already taken')
    if User.query.filter_by(email=email).first():
        return err('Email already registered')

    user = User(username=username, email=email, name=name, role='student',
                password=generate_password_hash(password),
                phone=data.get('phone'), department=data.get('department'))
    db.session.add(user)
    db.session.commit()
    return jsonify(message='Registered successfully, please login'), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(username=data.get('username', '')).first()
    if not user or not check_password_hash(user.password, data.get('password', '')):
        return err('Wrong username or password', 401)
    if user.status != 'Active':
        return err('Your account is not active, contact admin', 403)

    token = create_access_token(identity=str(user.id), additional_claims={'role': user.role})
    return jsonify(token=token, user=user.to_dict())


@auth_bp.route('/profile', methods=['GET'])
@role_required('admin', 'examiner', 'student')
def get_profile():
    return jsonify(User.query.get(current_user_id()).to_dict())


@auth_bp.route('/profile', methods=['PUT'])
@role_required('admin', 'examiner', 'student')
def update_profile():
    user = User.query.get(current_user_id())
    data = request.get_json() or {}

    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    if not name or '@' not in email:
        return err('Valid name and email are required')
    other = User.query.filter(User.email == email, User.id != user.id).first()
    if other:
        return err('Email already used by someone else')

    user.name = name
    user.email = email
    user.phone = data.get('phone')
    user.department = data.get('department')
    if data.get('password'):
        if len(data['password']) < 6:
            return err('Password must have at least 6 characters')
        user.password = generate_password_hash(data['password'])
    db.session.commit()
    return jsonify(message='Profile updated', user=user.to_dict())
