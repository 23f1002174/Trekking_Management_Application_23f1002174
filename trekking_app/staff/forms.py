from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Regexp


class TrekStatusForm(FlaskForm):
    status = SelectField(
        "Update Trek Status",
        choices=[
            ("open", "Open"),
            ("closed", "Closed"),
            ("started", "Started"),
            ("completed", "Completed"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Update Status")


class SlotsUpdateForm(FlaskForm):
    available_slots = IntegerField(
        "Available Slots",
        validators=[
            DataRequired(message="Please enter a valid number of slots."),
            NumberRange(min=0, message="Available slots cannot be negative."),
        ],
    )
    submit = SubmitField("Update Slots")


class StaffProfileForm(FlaskForm):
    full_name = StringField(
        "Full Name",
        validators=[
            DataRequired(),
            Length(min=2, max=120, message="Name must be between 2 and 120 characters."),
        ],
    )
    phone = StringField(
        "Phone Number",
        validators=[
            DataRequired(),
            Regexp(r"^\d{10}$", message="Enter a valid 10-digit phone number."),
        ],
    )
    submit = SubmitField("Save Changes")
