from flask import Flask, current_app, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from itsdangerous import Serializer, BadSignature, SignatureExpired
from forms import RegistrationForm, LoginForm, DashboardForm, ContactForm, ForgotPasswordForm, ResetPasswordForm
from flask_bcrypt import Bcrypt
from flask_mail import Message, Mail
from twilio.rest import Client
import os
import secrets
from dotenv import load_dotenv
import logging
from models import db, User, Contact

app = Flask(__name__, template_folder='templates')

secret_key = secrets.token_hex(16)

# Configure the app
app.config['SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', 'postgresql:///greetings'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Load environment variables from .env file
load_dotenv()


# Retrieve the Twilio API credentials from environment variables
TWILIO_ACCOUNT_SID = os.getenv('ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Initialize the Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

logging.basicConfig(level=logging.DEBUG)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Gmail SMTP server
app.config['MAIL_PORT'] = 587  # Gmail SMTP port
app.config['MAIL_USERNAME'] = 'nortonjulian@gmail.com'  # Your Gmail email address
app.config['MAIL_PASSWORD'] = 'dilt etdd rojh rqjj'  # Your Gmail password or an "App Password" if enabled
app.config['MAIL_USE_TLS'] = True  # Use TLS for secure communication
app.config['MAIL_USE_SSL'] = False  # Disable SSL

# Initialize Flask-Mail
mail = Mail(app)

# # Initialize the database
# db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

def connect_db(app):
    db.app = app
    db.init_app(app)

# Call connect_db to associate the db instance with your app
connect_db(app)

# Initialize the login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()  # Create an instance of your registration form

    if request.method == 'POST':
        # Check if the form is being submitted (for debugging purposes)
        print("Form submitted")

        if form.validate_on_submit():
            # Check if form validation passes (for debugging purposes)
            print("Form is valid")

            username = form.username.data
            email = form.email.data
            password = form.password.data
            first_name = form.first_name.data
            last_name = form.last_name.data

            # Create a new user object
            new_user = User(username=username, email=email, password=password, first_name=first_name, last_name=last_name)

            # Add the user to the database
            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            # If there are validation errors, print them (for debugging purposes)
            print(form.errors)

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user:
            stored_hashed_password = user.password

            # Verify that the stored hashed password is not empty
            if stored_hashed_password:
                # Removing leading/trailing spaces from submitted password
                submitted_password = password.strip()
                stored_hashed_password = stored_hashed_password.strip()

                # Check if the submitted password matches the stored hashed password
                if stored_hashed_password == submitted_password:
                    login_user(user)
                    flash(f'Welcome, {user.username}!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Login failed. Please check your credentials.', 'danger')
            else:
                flash('Stored hashed password is empty. Please check your account.', 'danger')
        else:
            flash('User not found. Please check your username.', 'danger')

    return render_template('login.html', form=form)

# Logout route
@app.route('/logout')
@login_required
def logout():
    if current_user.is_authenticated:
        username = current_user.username
        logout_user()
        flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('index'))


# Send message route
@app.route('/send', methods=['GET', 'POST'])
@login_required
def send_message():
    form = DashboardForm()

    if request.method == 'POST':
        selected_contact_ids = request.form.getlist('selected_contacts')
        message_body = request.form['message']

        # Fetch selected contacts from the database
        selected_contacts = Contact.query.filter(Contact.id.in_(selected_contact_ids)).all()

        try:
            # Iterate through selected contacts and send messages
            for contact in selected_contacts:
                # Implement Twilio message sending here for each contact
                twilio_client.messages.create(
                    body=message_body,
                    from_=TWILIO_PHONE_NUMBER,  # Your Twilio phone number
                    to=contact.number  # Use the contact's phone number
                )

            flash('Messages sent successfully!', 'success')
        except Exception as e:
            flash(f'Failed to send messages: {str(e)}', 'danger')

        return redirect(url_for('dashboard'))

    return render_template('dashboard.html', contacts=selected_contacts, form=form)


# Add a route to display and edit contacts
@app.route('/contacts', methods=['GET', 'POST'])
@login_required
def contacts():
    form = ContactForm()
    if request.method == 'POST':
        # Handle contact creation/editing here
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        number = request.form['number']

        if request.form.get('contact_id'):
            # If a contact_id is present, it's an edit request
            contact_id = int(request.form['contact_id'])
            contact = Contact.query.get(contact_id)
            contact.first_name = first_name
            contact.last_name = last_name
            contact.number = number
        else:
            # Otherwise, it's a new contact creation request
            contact = Contact(user_id=current_user.id, first_name=first_name, last_name=last_name, number=number)
            db.session.add(contact)

        db.session.commit()
        flash('Contact saved successfully!', 'success')

    user_contacts = current_user.contacts
    return render_template('contacts.html', contacts=user_contacts, form=form)

# Add a route to delete contacts
@app.route('/delete_contact/<int:contact_id>', methods=['POST'])
@login_required
def delete_contact(contact_id):
    contact = Contact.query.get(contact_id)

    if contact and contact.user_id == current_user.id:
        db.session.delete(contact)
        db.session.commit()
        flash('Contact deleted successfully!', 'success')

    return redirect(url_for('contacts'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_contacts = current_user.contacts
    form = DashboardForm()

    return render_template('dashboard.html', contacts=user_contacts, form=form)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            send_password_reset_email(user)  # Call the send_password_reset_email function
            flash('Check your email for the instructions to reset your password', 'info')
            return redirect(url_for('login'))
        flash('Email not found. Please check your email address.', 'danger')

    return render_template('forgot_password.html', form=form)

def verify_reset_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token)['reset_password']
        return user_id
    except SignatureExpired:
        # Token expired
        return None
    except BadSignature:
        # Invalid token
        return None

# Add this route to your app.py
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user_id = verify_reset_token(token)

    if not user_id:
        flash('Invalid or expired token. Please request a new one', 'danger')
        return redirect(url_for('forgot_password'))

    form = ResetPasswordForm()  # Create a form for resetting the password

    if form.validate_on_submit():
        user = User.query.get(user_id)
        if user:
            user.password = form.password.data
            db.session.commit()
            flash('Your password has been reset. You can now log in with your new password.', 'success')
            return redirect(url_for('login'))
        else:
            flash('User not found', 'danger')

    return render_template('reset_password.html', form=form)

def send_password_reset_email(user):
    # Create a token with a serializer
    s = Serializer(current_app.config['SECRET_KEY'])
    token = s.dumps({'reset_password': user.id})


    # Create the reset password link using 'url_for'
    reset_url = url_for('reset_password', token=token, _external=True)

    msg = Message('Reset Your Password', sender='noreply@example.com', recipients=[user.email])
    msg.body = f'''
    To reset your password, visit the following link:
    {reset_url}

    If you didn't request this email, simply ignore it.
    '''
    mail.send(msg)


# app.debug = True

print("Before main block")
if __name__ == '__main__':
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    app.run(debug=True, use_reloader=False)
