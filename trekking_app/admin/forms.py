from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError


DIFFICULTY_CHOICES = [
    ("easy", "Easy"),
    ("moderate", "Moderate"),
    ("hard", "Hard"),
]

TREK_STATUS_CHOICES = [
    ("closed", "Closed"),
    ("open", "Open"),
    ("started", "Started"),
    ("completed", "Completed"),
]


class TrekForm(FlaskForm):
    name = StringField("Trek Name", validators=[DataRequired(), Length(min=3, max=150)])
    location = StringField("Location", validators=[DataRequired(), Length(min=2, max=150)])
    difficulty = SelectField("Difficulty", choices=DIFFICULTY_CHOICES, validators=[DataRequired()])
    duration_days = IntegerField(
        "Duration (Days)",
        validators=[DataRequired(), NumberRange(min=1, max=60)],
    )
    total_slots = IntegerField(
        "Total Slots",
        validators=[DataRequired(), NumberRange(min=1, max=500)],
    )
    start_date = DateField("Start Date", validators=[DataRequired()], format="%Y-%m-%d")
    end_date = DateField("End Date", validators=[DataRequired()], format="%Y-%m-%d")
    assigned_staff_id = SelectField(
        "Assigned Staff",
        coerce=int,
        validators=[],
        choices=[(0, "Unassigned")],
    )
    status = SelectField("Status", choices=TREK_STATUS_CHOICES, validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Length(max=1000)])
    submit = SubmitField("Save Trek")

    def validate_end_date(self, field):
        if self.start_date.data and field.data and field.data < self.start_date.data:
            raise ValidationError("End date cannot be earlier than start date.")
