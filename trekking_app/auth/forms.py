from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from trekking_app.models import User
from trekking_app.services.auth_service import normalize_email, normalize_phone


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=3, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Phone Number", validators=[DataRequired(), Length(min=10, max=20)])
    role = SelectField(
        "I am a",
        choices=[
            ("user", "User (Trekker)"),
            ("staff", "Trek Staff"),
        ],
        validators=[DataRequired()],
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create Account")

    def validate_email(self, field):
        existing_user = User.query.filter_by(email=normalize_email(field.data)).first()
        if existing_user:
            raise ValidationError("An account with this email already exists.")

    def validate_phone(self, field):
        normalized_phone = normalize_phone(field.data)
        if len(normalized_phone) < 10:
            raise ValidationError("Enter a valid phone number with at least 10 digits.")


class LogoutForm(FlaskForm):
    submit = SubmitField("Logout")
