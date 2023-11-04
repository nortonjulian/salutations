from datetime import datetime, timedelta
from sqlalchemy import DateTime
import pytz
from flask import app, current_app
from database import db
from flask_bcrypt import Bcrypt
from flask_login import UserMixin  # Import UserMixin
from itsdangerous import TimedSerializer as Serializer
import os

# secret_key = current_app.config['SECRET_KEY']

# Create an instance of SQLAlchemy
# db = SQLAlchemy()

bcrypt = Bcrypt()

class User(db.Model, UserMixin):  # Inherit from UserMixin here
    """Table of users"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(60), nullable=False)

    # Add a one-to-many relationship to link users and contacts
    contacts = db.relationship('Contact', backref='user', lazy=True)

    # Define a one-to-many relationship to link uers and conversations
    conversations = db.relationship('Conversation', backref='user', lazy='select')

    twilio_number_association = db.relationship('TwilioNumberAssociation', back_populates='user', lazy=True)

    @classmethod
    def signup(cls, username, password, first_name, last_name, email):
        """Signup user"""
        # Generate a new salt and hash the password
        hashed_pwd = bcrypt.generate_password_hash(password).decode('utf-8')
        print(f'Stored hashed Password: {hashed_pwd}')

        user = User(username=username, email=email, first_name=first_name, last_name=last_name, password=hashed_pwd)

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        user = cls.query.filter_by(username=username).first()

        if user:
            app.logger.debug(f"Stored salt: {user.password}")
            app.logger.debug(f"Submitted password: {password}")

            if bcrypt.check_password_hash(user.password, password):
                return user

        return None

    @classmethod
    def check_password(self, password):
        """Check if the provided password matches the stored password hash."""
        return bcrypt.check_password_hash(self.password, password)

    def get_reset_password_token(self, expires_in=600):
        """
        Generate a token for resetting the user's password.
        :param expires_in: The expiration time for the token in seconds (default is 10 minutes).
        :return: The generated token as a string.
        """
        with current_app.app_context():
            salt = os.urandom(16)
            s = Serializer(current_app.config['SECRET_KEY'])
            return s.dumps({'reset_password': self.id}, salt=salt)

    @staticmethod
    def verify_reset_password_token(token):
        """
        Verify a password reset token and return the associated user.
        :param token: The token to verify.
        :return: The user associated with the token, or None if the token is invalid.
        """
        with current_app.app_context():
            s = Serializer(current_app.config['SECRET_KEY'])
            try:
                data = s.loads(token)
            except:
                return None
            return User.query.get(data['reset_password'])

class Contact(db.Model):
    """Table of contacts"""

    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    number = db.Column(db.String(20), nullable=False, unique=True)

    # def __init__(self, user_id, first_name, last_name, number):
    #     self.user_id = user_id
    #     self.first_name = first_name
    #     self.last_name = last_name
    #     self.number = number

    @classmethod
    def add(cls, user_id, first_name, last_name, number):
        """Add Contacts"""

        contact = cls(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            number=number,
        )
        db.session.add(contact)
        return contact

class Conversation(db.Model):
    """Table of conversations between users"""

    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender_number = db.Column(db.String, nullable=False)
    receiver_number = db.Column(db.String, nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)

    # Update the relationship to link conversations and messages
    messages = db.relationship('Message', lazy=True)
    messages_read = db.Column(db.Boolean, default=False)

    def __init__(self, sender_number, receiver_number, user_id=None, contact_id=None):
        self.user_id = user_id
        self.sender_number = sender_number
        self.receiver_number = receiver_number
        self.contact_id = contact_id

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    receiver_number = db.Column(db.String, nullable=False)
    timestamp = db.Column(DateTime, default=datetime.utcnow)
    messages_read = db.Column(db.Boolean, default=False)

    # Define the relationship to the User model for the sender
    sender = db.relationship('User', foreign_keys=[sender_id])

    # Remove the back_populates and backref from the conversation relationship
    conversation = db.relationship('Conversation', back_populates='messages', overlaps='messages')

    # def formatted_timestamp(self):

    #     desired_timezone = pytz.timezone('America/Los_Angeles')
    #     localized_time = self.timestamp.astimezone(desired_timezone)

    #     formatted_time = localized_time.strftime("%A, %I:%M %p, %B %d, %Y")
    #     return formatted_time.lstrip("0").replace(" 0", " ")

    def formatted_timestamp(self):
        # Subtract 6 hours from the timestamp
        six_hours_ago = self.timestamp - timedelta(hours=5)

        desired_timezone = pytz.timezone('America/Los_Angeles')
        localized_time = six_hours_ago.astimezone(desired_timezone)

        formatted_time = localized_time.strftime("%A, %I:%M %p, %B %d, %Y")
        return formatted_time.lstrip("0").replace(" 0", " ")


class TwilioNumberAssociation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    twilio_number = db.Column(db.String(15), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Specify the relationship explicitly using 'primaryjoin'
    user = db.relationship('User', back_populates='twilio_number_association', primaryjoin="TwilioNumberAssociation.user_id == User.id")

    def __init__(self, twilio_number, user_id):
        self.twilio_number = twilio_number
        self.user_id = user_id




# def connect_db(app):
#     db.app = app
#     db.init_app(app)
