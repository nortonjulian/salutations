from datetime import datetime
from flask import app, current_app
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin  # Import UserMixin
from itsdangerous import TimedSerializer as Serializer
import os

# secret_key = current_app.config['SECRET_KEY']

# Create an instance of SQLAlchemy
db = SQLAlchemy()

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
            return User.query.get(data.get('reset_password'))

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


# def connect_db(app):
#     db.app = app
#     db.init_app(app)
