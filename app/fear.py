"""Fear blueprint"""
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required, logout_user
from . import db
from .models import Fear
from .forms import FearForm
from .comment_moderation import analyze_toxicity, add_toxic_warning

fear_bp = Blueprint('fear_bp', __name__)

@fear_bp.route('/create_fear', methods=['GET', 'POST'])
@login_required
def create_fear():
    """creating fear"""
    form = FearForm()
    if form.validate_on_submit():
        # Combine title and description for toxicity check
        full_text = f"{form.title.data} {form.description.data}"
        toxicity = analyze_toxicity(full_text)

        if toxicity["is_toxic"]:
            add_toxic_warning(current_user)

            now = datetime.utcnow()
            if current_user.login_block_until and current_user.login_block_until > now:
                wait = (current_user.login_block_until - now).seconds // 60
                flash(
                    f"You’ve reached 3 toxic-post warnings. "
                    f"Your account is blocked for {wait} minutes.",
                    "danger"
                )
                logout_user()
                return redirect(url_for('auth_bp.login'))

            flash("Your post was flagged as inappropriate. Try revising it.", "danger")
            return render_template('create_fear.html', form=form)

        # If not toxic, save the fear
        fear = Fear(
            title=form.title.data,
            description=form.description.data,
            author=current_user,
            created_at=datetime.utcnow(),
            is_toxic=False,
            toxicity_score=toxicity["score"]
        )

        db.session.add(fear)
        db.session.commit()
        flash('Your fear has been created!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('create_fear.html', form=form)

@fear_bp.route('/edit_fear/<int:fear_id>', methods=['GET', 'POST'])
@login_required
def edit_fear(fear_id):
    """Editing fear"""
    fear = Fear.query.get_or_404(fear_id)
    if fear.author != current_user:
        flash('You are not authorized to edit this post!', 'danger')
        return redirect(url_for('main.dashboard'))

    form = FearForm(obj=fear)  # Prefill form with existing data
    if form.validate_on_submit():
        # Combine new title and description for toxicity check
        full_text = f"{form.title.data} {form.description.data}"
        toxicity = analyze_toxicity(full_text)

        if toxicity["is_toxic"]:
            add_toxic_warning(current_user)

            now = datetime.utcnow()
            if current_user.login_block_until and current_user.login_block_until > now:
                wait = (current_user.login_block_until - now).seconds // 60
                flash(
                    f"You’ve reached 3 toxic-post warnings. "
                    f"Your account is blocked for {wait} minutes.",
                    "danger"
                )
                logout_user()
                return redirect(url_for('auth_bp.login'))

            flash("🚫 Your edited post was flagged as inappropriate.", "danger")
            return render_template('fear_edit.html', form=form, fear=fear)

        # If not toxic, update fear fields and commit
        fear.title = form.title.data
        fear.description = form.description.data
        fear.is_toxic = False
        fear.toxicity_score = toxicity["score"]
        fear.updated_at = datetime.utcnow()  # optional: add updated_at field if you want
        db.session.commit()

        flash('Your fear has been updated!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('fear_edit.html', form=form, fear=fear)

@fear_bp.route('/delete_fear/<int:fear_id>', methods=['POST'])
@login_required
def delete_fear(fear_id):
    """Deleting fear"""
    fear = Fear.query.get_or_404(fear_id)
    if fear.author != current_user:
        flash('You are not authorized to delete this post!', 'danger')
        return redirect(url_for('main.dashboard'))
    db.session.delete(fear)
    db.session.commit()
    flash('Your fear has been deleted!', 'success')
    return redirect(url_for('main.dashboard'))

@fear_bp.route('/fear/<int:fear_id>')
@login_required
def fear_detail(fear_id):
    """fear details"""
    fear = Fear.query.get_or_404(fear_id)
    return render_template('fear_detail.html', fear=fear)
