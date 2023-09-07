from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, FieldList, HiddenField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class MessageForm(FlaskForm):
    """Form for adding/editing messages."""

    text = TextAreaField('text', validators=[DataRequired()])

class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])

class ContactAddForm(FlaskForm):
    """Form for adding contacts"""
    username = StringField('Username', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    number = IntegerField('Number', validators=[DataRequired()])
    hidden_number = HiddenField('Hidden Number')


class EditForm(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired()])
    recipients = FieldList(TextAreaField('Recipient'), min_entries=1)
