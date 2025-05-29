"""Auth Blueprint"""
from datetime import datetime
import os

from flask import Blueprint, render_template, redirect, session, url_for, flash, current_app
from flask_login import login_user, logout_user
from werkzeug.utils import secure_filename
from .models import User
from .forms import LoginForm, RegistrationForm
from .comment_moderation import reset_user_warnings
from . import db

auth_bp = Blueprint('auth_bp', __name__)

def allowed_file(filename):
    """Allowed file extension"""
    # Check if there's a period (.) in the filename to determine if it has an extension
    has_extension = '.' in filename
    if not has_extension:
        return False

    # Split the filename by the last period to isolate the file extension
    parts = filename.rsplit('.', 1)
    if len(parts) != 2:
        return False

    extension = parts[1].lower()

    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())

    if extension in allowed_extensions:
        return True
    else:
        return False

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registering"""
    form = RegistrationForm()

    # Checks if form was submitted via POST & All fields are valid
    if form.validate_on_submit():
        avatar_file = form.avatar.data
        avatar_filename = None

        if avatar_file:
            filename = secure_filename(avatar_file.filename)

            if not allowed_file(filename):
                flash("Invalid file type. Only PNG, JPG, JPEG, SVG, WEBP and GIF are allowed.", "danger")
                return redirect(url_for('auth_bp.register'))

            avatar_file.seek(0, os.SEEK_END)
            file_size = avatar_file.tell()
            avatar_file.seek(0)

            max_size = current_app.config['MAX_CONTENT_LENGTH']
            if file_size > max_size:
                flash(f"File too large. Max size is {max_size // (1024 * 1024)}MB.", "danger")
                return redirect(url_for('auth_bp.register'))

            # Save file
            avatar_filename = f"{form.username.data}_{filename}"
            avatar_folder = os.path.join(current_app.root_path, '..', 'static', 'avatars')
            os.makedirs(avatar_folder, exist_ok=True)
            avatar_path = os.path.join(avatar_folder, avatar_filename)
            avatar_file.save(avatar_path)

        # Save user to DB
        user = User(
            username=form.username.data,
            email=form.email.data,
            avatar=avatar_filename
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('auth_bp.login'))

    return render_template('register.html', form=form)

# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Log In"""
    form = LoginForm()
    if form.validate_on_submit():
        # 1) Fetch the user by username
        user = User.query.filter_by(username=form.username.data).first()

        # 2) If the user exists, check for a block
        if user:
            now = datetime.utcnow()
            # a) Still blocked?
            if user.login_block_until and user.login_block_until > now:
                wait = (user.login_block_until - now).seconds // 60
                flash(
                    f"Your account is blocked due to repeated toxic comments. "
                    f"Try again in {wait} minutes.",
                    "danger"
                )
                return redirect(url_for('auth_bp.login'))

            # b) Block expired — clear their warnings so they start fresh
            if user.login_block_until and user.login_block_until <= now:
                reset_user_warnings(user)

        # 3) Now do the regular password check
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            session.permanent = form.remember_me.data
            flash('Login Successful!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password.', 'danger')

    return render_template('login.html', form=form)

# Logout route
@auth_bp.route('/logout')
def logout():
    """Log out"""
    print("Logout triggered!")  # or use logging
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
