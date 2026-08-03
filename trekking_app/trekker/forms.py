from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError

from trekking_app.models import User
from trekking_app.services.auth_service import normalize_email, normalize_phone


class ProfileForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=3, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Phone Number", validators=[DataRequired(), Length(min=10, max=20)])
    submit = SubmitField("Save Profile")

    def __init__(self, original_user_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_user_id = original_user_id

    def validate_email(self, field):
        normalized_email = normalize_email(field.data)
        existing_user = User.query.filter_by(email=normalized_email).first()
        if existing_user and existing_user.id != self.original_user_id:
            raise ValidationError("An account with this email already exists.")

    def validate_phone(self, field):
        normalized_phone = normalize_phone(field.data)
        if len(normalized_phone) < 10:
            raise ValidationError("Enter a valid phone number with at least 10 digits.")
