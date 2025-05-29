"""Main blueprint"""
from datetime import datetime
import os

from flask import Blueprint, abort, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from flask_login import login_required, current_user, logout_user
from werkzeug.utils import secure_filename

from .forms import AvatarForm
from .models import db, Fear, Comment, User
from .auth import allowed_file
from .comment_moderation import analyze_toxicity, add_toxic_warning

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """selected user info"""
    selected_user_id = request.args.get('user_id') # getting id from url
    users = User.query.all()

    if current_user.is_authenticated:
        query = Fear.query.filter(Fear.user_id != current_user.id)

        #getting fears of a selected user
        if selected_user_id and selected_user_id.isdigit():
            query = query.filter(Fear.user_id == int(selected_user_id))

        fears = query.order_by(Fear.created_at.desc()).all()
    else:
        fears = [] # If the user is not logged in, show no fears.

    return render_template('index.html', fears=fears, users=users)

@main.route('/dashboard')
@login_required
def dashboard():
    """dashboard"""
    fears = Fear.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', fears=fears)
 
@main.route('/comment/<int:fear_id>', methods=['POST'])
@login_required
def add_comment(fear_id):
    content = request.form.get('content')
    
    toxicity = analyze_toxicity(content)
    if toxicity["is_toxic"]:
        # 1) record the warning
        add_toxic_warning(current_user)

        # 2) check if they’re now blocked
        now = datetime.utcnow()
        if current_user.login_block_until and current_user.login_block_until > now:
            # they just got blocked (3rd warning)
            wait = (current_user.login_block_until - now).seconds // 60
            flash(
                f"You’ve reached 3 toxic-comment warnings. "
                f"Your account is blocked for {wait} minutes.",
                "danger"
            )
            
            # immediately log them out and send to login
            logout_user()
            return redirect(url_for('auth_bp.login'))

        # otherwise, show the “inappropriate” modal as before
        return redirect(url_for('main.index', show_modal='comment_failed'))

    # If not toxic, save comment
    comment = Comment(
        content=content,
        user_id=current_user.id,
        fear_id=fear_id,
        is_toxic=False,
        toxicity_score=toxicity["score"]
    )
    db.session.add(comment)
    db.session.commit()

    flash("Your comment was added successfully!", "success")
    return redirect(url_for('main.index'))

# Edit Comment Route
@main.route('/comment/<int:comment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        content = request.form.get('content')

        # Check for empty content
        if not content:
            flash('🚫 Comment cannot be empty.', 'danger')
            return render_template('edit_comment.html', comment=comment)

        toxicity = analyze_toxicity(content)

        if toxicity["is_toxic"]:
            add_toxic_warning(current_user)

            now = datetime.utcnow()
            if current_user.login_block_until and current_user.login_block_until > now:
                wait = (current_user.login_block_until - now).seconds // 60
                flash(
                    f"You’ve reached 3 toxic-comment warnings. "
                    f"Your account is blocked for {wait} minutes.",
                    "danger"
                )
                logout_user()
                return redirect(url_for('auth_bp.login'))

            flash('🚫 Your edited comment was flagged as inappropriate.', 'danger')
            return render_template('edit_comment.html', comment=comment)

        # If not toxic, update comment and commit
        comment.content = content
        comment.is_toxic = False
        comment.toxicity_score = toxicity["score"]
        db.session.commit()

        flash('Comment updated!', 'success')
        return redirect(url_for('main.index'))

    return render_template('edit_comment.html', comment=comment)

# Delete Comment Route
@main.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id:
        abort(403)
    
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted!', 'success')
    return redirect(url_for('main.index'))

@main.route('/upload_avatar', methods=['GET', 'POST'])
@login_required
def upload_avatar():
    """updating avatar"""
    form = AvatarForm()

    if form.validate_on_submit():
        avatar_file = form.avatar.data
        if avatar_file:
            filename = secure_filename(avatar_file.filename)

            if not allowed_file(filename):
                flash("Invalid file type. Only PNG, JPG, JPEG, SVG, WEBP and GIF are allowed.", "danger")
                return redirect(url_for('main.upload_avatar'))

            # Check file size manually
            avatar_file.seek(0, os.SEEK_END)
            file_size = avatar_file.tell()
            avatar_file.seek(0)

            max_size = current_app.config.get('MAX_CONTENT_LENGTH', 2 * 1024 * 1024)
            if file_size > max_size:
                flash(f"File too large. Max size is {max_size // (1024 * 1024)}MB.", "danger")
                return redirect(url_for('main.upload_avatar'))

            avatar_filename = f"{current_user.username}_{filename}"
            avatar_folder = os.path.join(current_app.root_path, '..', 'static', 'avatars')
            os.makedirs(avatar_folder, exist_ok=True)
            avatar_path = os.path.join(avatar_folder, avatar_filename)

            # Delete old avatar if it exists
            if current_user.avatar:
                old_avatar_path = os.path.join(avatar_folder, current_user.avatar)
                if os.path.exists(old_avatar_path) and current_user.avatar != avatar_filename:
                    os.remove(old_avatar_path)

            # Save the new file
            avatar_file.save(avatar_path)

            # Update user avatar in DB
            current_user.avatar = avatar_filename
            db.session.commit()

            flash('Avatar updated successfully ✅', 'success')
            return redirect(url_for('main.dashboard'))

    return render_template('upload_avatar.html', form=form)

# Route to serve uploaded avatars
@main.route('/avatars/<filename>')
def get_avatar(filename):
    """Getting user avatar"""
    return send_from_directory(
        os.path.join(current_app.root_path, '..', 'static', 'avatars'),
          secure_filename(filename)
    )
