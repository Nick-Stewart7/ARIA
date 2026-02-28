from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
import os
from datetime import timedelta

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
bcrypt = Bcrypt()

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Configuration
    if config_name == 'testing':
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
        app.config['WTF_CSRF_ENABLED'] = True
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from ARIA.artifacts.code.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.tasks import tasks_bp
    from routes.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        from ARIA.artifacts.code.models import User, Role
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin', description='Administrator')
            user_role = Role(name='user', description='Regular User')
            db.session.add(admin_role)
            db.session.add(user_role)
            db.session.commit()
        
        admin_user = User.query.filter_by(email='admin@example.com').first()
        if not admin_user:
            from flask_bcrypt import generate_password_hash
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                role_id=admin_role.id
            )
            db.session.add(admin_user)
            db.session.commit()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)