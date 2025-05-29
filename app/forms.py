"""Forms"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, BooleanField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo # confirm password matches the password
from flask_wtf.file import FileRequired, FileAllowed

# User Registration Form
class RegistrationForm(FlaskForm):
    """Reg form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    avatar = FileField('Avatar')  # Add this field to handle avatar upload
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    """Login form"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')  # Add remember me field
    submit = SubmitField('Login')

# Fear Creation and Editing Form
class FearForm(FlaskForm):
    """Fear form"""
    title = StringField('Fear Title', validators=[DataRequired(), Length(min=5, max=120)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Save Fear')

# Comment Form for Fear
class CommentForm(FlaskForm):
    """Comment form"""
    content = TextAreaField('Comment', validators=[DataRequired(), Length(min=2)])
    submit = SubmitField('Add Comment')

class AvatarForm(FlaskForm):
    """Avatar form"""
    avatar = FileField('Profile Picture', validators=[
        FileRequired(),
        FileAllowed(['png', 'jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'], 'Images only!')
    ])
