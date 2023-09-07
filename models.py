from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()


class User(db.Model):
    """table of users"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.Text, nullable=False)
    last_name = db.Column(db.Text, nullable=False)
    username= db.Column(db.Text, nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False, unique=True)
    email = db.Column(db.Text, nullable=False, unique=True)

    @classmethod
    def signup(cls, username, password, first_name, last_name, email):
        """Signup user"""

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(username=username, email=email, first_name=first_name, last_name=last_name, password=hashed_pwd)

        db.session.add(user)
        return user


    @classmethod
    def authenticate(cls, username, password):

        user = cls.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            return user

        return None

class Contacts(db.Model):
    """table of contacts"""

    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    username= db.Column(db.Text, nullable=False, unique=True)
    first_name = db.Column(db.Text, nullable=False)
    last_name = db.Column(db.Text, nullable=False)
    number = db.Column(db.Integer, nullable=False, unique=True)

    @classmethod
    def add(cls, user_id, first_name, last_name, number):
        """Add Contacts"""

        contact = Contacts(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            number=number,
        )
        db.session.add(contact)
        return contact


def connect_db(app):

    db.app = app
    db.init_app(app)
