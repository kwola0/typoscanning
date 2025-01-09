import re
from flask_wtf import FlaskForm
from wtforms import PasswordField
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, ValidationError
from wtforms.validators import EqualTo, Length


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class AlertForm(FlaskForm):
    alert_email = StringField("Alert Email", validators=[Email(), Optional()])
    submit = SubmitField("Save Email")


def validate_cron(form, field):
    cron_pattern = (r"^((\d+,)+\d+|\d+|\*|\*\/\d+|\d+-\d+|\?|L|W|#)+\s+((\d+,"
                    r")+\d+|\d+|\*|\*\/\d+|\d+-\d+|\?|L|W|#)+\s+((\d+,)+\d+|\d+|\*|\*\/\d+|\d+-\d+|\?|L|W|#)+\s+(("
                    r"\d+,)+\d+|\d+|\*|\*\/\d+|\d+-\d+|\?|L|W|#)+\s+((\d+,)+\d+|\d+|\*|\*\/\d+|\d+-\d+|\?|L|W|#)(\s+("
                    r"(\d+,)+\d+|\d+|\*|\*\/\d+|\d+-\d+|\?|L|W|#))?$")
    if form.frequency.data == "custom" and not re.match(cron_pattern, field.data):
        raise ValidationError("Invalid cron expression. Example: * * * * *")


class AlertForm(FlaskForm):
    alert_email = StringField("Alert Email", validators=[Email(), Optional()])
    submit = SubmitField("Save Email")


class ScanSettingsForm(FlaskForm):
    domain = SelectField(
        'Domain',
        choices=[],
        validators=[DataRequired()]
    )
    frequency = SelectField(
        'Scan Frequency',
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('custom', 'Custom')
        ],
        validators=[DataRequired()]
    )
    custom_cron = StringField(
        'Custom Cron Schedule',
        validators=[DataRequired()])
    custom_cron = StringField('Custom Cron', validators=[Optional(), validate_cron])

    submit = SubmitField('Save Settings')
