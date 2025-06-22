from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///student_portal.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from .models import User, Admin
    from . import auth, dashboard
    app.register_blueprint(auth.auth)
    app.register_blueprint(dashboard.dashboard)

    @login_manager.user_loader
    def load_user(user_id):
        # Try to load user from both User and Admin tables
        user = User.query.get(int(user_id))
        if user:
            return user
        return Admin.query.get(int(user_id))

    def init_db():
        db.create_all()
        # Create admin user if it doesn't exist
        from werkzeug.security import generate_password_hash
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(
                username='admin',
                password=generate_password_hash('admin123'),
                email='admin@example.com'
            )
            db.session.add(admin)
            try:
                db.session.commit()
                print("Admin user created successfully")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating admin user: {e}")

    with app.app_context():
        init_db()

    return app 