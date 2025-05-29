"""__init__.py"""
import os
from datetime import datetime, timedelta
from flask import Flask, request,redirect, url_for, flash
from flask_login import LoginManager, current_user, logout_user
from flask_migrate import Migrate

from .models import db
from .models import User

from .auth  import auth_bp
from .main  import main as main_bp
from .fear  import fear_bp

login_manager = LoginManager()

def create_app():
    """Creating App"""
    # Tell Flask it can use the instance folder
    app = Flask(__name__, instance_relative_config=True, template_folder='../templates', static_folder='../static')

    # creates instance/ folder
    os.makedirs(app.instance_path, exist_ok=True)

    app.config['SECRET_KEY'] = 'supersecretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"sqlite:///{os.path.join(app.instance_path, 'site.db')}"
    )

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
    # If not selecting remember_me, session expires after 30 min of inaction
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB max upload
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}

    db.init_app(app)

    Migrate(app, db)

    login_manager.init_app(app)
    login_manager.login_view = 'auth_bp.login'
    login_manager.logout_view = 'auth_bp.logout'

    # Retrieving user_id from db for Flask Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # GLOBAL BLOCK CHECK
    @app.before_request
    def enforce_login_block():
        # For debugging (optional)
        print(f"Checking request to: {request.endpoint}")

        # Allowlist: login, logout, register, static files
        allowed_endpoints = ['auth_bp.login', 'auth_bp.logout', 'auth_bp.register', 'static']
        if request.endpoint in allowed_endpoints:
            return

        if (current_user.is_authenticated
            and current_user.login_block_until
            and current_user.login_block_until > datetime.utcnow()):
            
            logout_user()
            flash("You are temporarily blocked. Try again later.", "danger")
            return redirect(url_for('auth_bp.login'))
        
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(fear_bp)

    # Custom Jinja filter for formatting datetime values in templates
    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%H:%M %d/%m/%Y'):

        if value is None:
            return ""

        if isinstance(value, str):
            value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

        # Add a time difference of 5 hours to convert to Almaty time
        almaty_time = value + timedelta(hours=5)

        return almaty_time.strftime(format)

    return app
