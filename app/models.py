"""Models"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin #Provides functionality for user authentication in flask_login

db = SQLAlchemy() #initializes the SQLAlchemy extension in your Flask app.

class User(UserMixin, db.Model):
    """User table"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    fears = db.relationship('Fear', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    avatar = db.Column(db.String(120), nullable=True)

    # WARNING COUNTS
    toxic_warning_count = db.Column(db.Integer, default=0, nullable=False)
    last_warning_time  = db.Column(db.DateTime, nullable=True)
    login_block_until  = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        """hashing password"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """cheking password"""
        return check_password_hash(self.password_hash, password)

class Fear(db.Model):
    """Fear table"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_toxic = db.Column(db.Boolean, default=False)
    toxicity_score = db.Column(db.Float, default=0.0)
    
    comments = db.relationship('Comment', backref='fear', lazy=True, cascade="all, delete-orphan")

class Comment(db.Model):
    """Comment table"""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fear_id = db.Column(db.Integer, db.ForeignKey('fear.id'), nullable=False)
    is_toxic = db.Column(db.Boolean, default=False)
    toxicity_score = db.Column(db.Float, default=0.0)
