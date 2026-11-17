import os
from datetime import timedelta
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash
from models.models import db, User

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def create_admin():
    # only one admin, created from code (no registration for admin)
    if User.query.filter_by(role='admin').first():
        return
    admin = User(username=os.environ.get('ADMIN_USERNAME', 'admin'),
                 email=os.environ.get('ADMIN_EMAIL', 'admin@emp.com'),
                 name='Administrator', role='admin',
                 password=generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123')))
    db.session.add(admin)
    db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'emp.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'emp-dev-secret-key-1234567890abcdef')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)

    CORS(app)
    db.init_app(app)
    JWTManager(app)

    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.examiner import examiner_bp
    from routes.student import student_bp
    for bp in (auth_bp, admin_bp, examiner_bp, student_bp):
        app.register_blueprint(bp)

    # tables are created from the models, nothing is created by hand
    with app.app_context():
        db.create_all()
        create_admin()
    return app


if __name__ == '__main__':
    create_app().run(debug=True, port=5000)
