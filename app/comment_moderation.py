from datetime import datetime, timedelta
from transformers import pipeline
from .models import db

toxicity_analyzer = pipeline(
    "text-classification",
    model="unitary/toxic-bert",
    return_all_scores=False  # Simplifies output
)

def analyze_toxicity(text):
    result = toxicity_analyzer(text)[0]
    score = float(result["score"])
    
    # Only consider it toxic if BOTH:
    # 1. The label is "toxic" 
    # 2. The score is above our threshold (0.9)
    is_toxic = (result["label"] == "toxic") and (score > 0.7)
    
    return {
        "is_toxic": is_toxic,
        "score": score
    }

def add_toxic_warning(user, now=None, block_minutes=5, reset_after_hours=6):
    """Increment a user’s warning count; if ≥3 within reset_after_hours, block login."""
    now = now or datetime.utcnow()

    # if last warning is “stale,” start over
    if not user.last_warning_time \
       or (now - user.last_warning_time) > timedelta(hours=reset_after_hours):
        user.toxic_warning_count = 1
    else:
        user.toxic_warning_count += 1

    user.last_warning_time = now

    # if they’ve hit 3 warnings in that window, block
    if user.toxic_warning_count >= 3:
        user.login_block_until = now + timedelta(minutes=block_minutes)

    db.session.commit()


def reset_user_warnings(user):
    user.toxic_warning_count = 0
    user.last_warning_time  = None
    user.login_block_until  = None
    db.session.commit()