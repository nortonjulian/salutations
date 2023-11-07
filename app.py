# Add this at the beginning of your app.py
print("Flask application started")
from datetime import datetime
from flask import Flask, current_app, render_template, redirect, url_for, flash, request, abort, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from itsdangerous import Serializer, BadSignature, SignatureExpired
from forms import RegistrationForm, LoginForm, DashboardForm, ContactForm, ForgotPasswordForm, ResetPasswordForm, ResponseForm
from flask_bcrypt import Bcrypt
from flask_mail import Message, Mail
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import text
from functools import wraps
from sqlalchemy import and_
import os
import pytz
from twilio.rest import Client
from database import db
import secrets
from dotenv import load_dotenv
import logging
from models import User, Contact, Conversation, Message, TwilioNumberAssociation

app = Flask(__name__, template_folder='templates')
# db = SQLAlchemy()

csrf = CSRFProtect(app)
csrf.init_app(app)

app.config.update(WTF_CSRF_ENABLED=False,
                  WTF_CSRF_METHODS=['POST'])



app.config['WTF_CSRF_EXEMPT_ROUTES'] = ['/incoming_sms']

secret_key = secrets.token_hex(16)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = 'view'

# Configure the app
app.config['SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', 'postgresql:///salutations'))
app.config['SQLALCHEMY_ECHO'] = True

db.init_app(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Load environment variables from .env file
load_dotenv()

# Enable SQLAlchemy debugging
app.config['SQLALCHEMY_ECHO'] = True

# Retrieve the Twilio API credentials from environment variables
TWILIO_ACCOUNT_SID = os.getenv('ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
print("TWILIO_ACCOUNT_SID:", TWILIO_ACCOUNT_SID)
print("TWILIO_AUTH_TOKEN:", TWILIO_AUTH_TOKEN)

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

# def connect_db(app):
#     db.app = app
#     db.init_app(app)

# Call connect_db to associate the db instance with your app
# connect_db(app)

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

@app.route('/send', methods=['GET', 'POST'])
@login_required
def send_message():
    form = DashboardForm()
    selected_contacts = []

    if request.method == 'POST':
        selected_contact_ids = request.form.getlist('selected_contacts')
        message_body = request.form['message']

        # Check if manual_number is present in the form data
        manual_number = request.form.get('manual_number')

        if manual_number:
            # Send the message to the manually entered number

            existing_conversation = Conversation.query.filter(
                text("conversations.sender_number = :sender_number AND conversations.receiver_number = :receiver_number")
            ).params(
                sender_number=TWILIO_PHONE_NUMBER,
                receiver_number=int(manual_number),
            ).first()

            if existing_conversation:
                conversation_id = existing_conversation.id
                print("Using existing conversation")
            else:
                print("Creating new conversation")
                new_conversation = Conversation(
                    sender_number=TWILIO_PHONE_NUMBER,
                    receiver_number=manual_number,
                    user_id=current_user.id,
                    contact_id=None,
                )

                db.session.add(new_conversation)
                db.session.commit()
                conversation_id = new_conversation.id
            print("$$$$$$$$$$$$$$$$$$$$$ - Outgoing")
            print(conversation_id)

            sender_user_id = current_user.id
            print("Sender_User_ID:", sender_user_id)
            new_message = Message(
                 content=message_body,
                 conversation_id=conversation_id,
                 sender_id=sender_user_id,
                 receiver_number=manual_number,
                 timestamp=datetime.now(),
                 read=False
            )

            db.session.add(new_message)

            try:
                twilio_client.messages.create(
                    body=message_body,
                    from_=TWILIO_PHONE_NUMBER,
                    to=manual_number
                )
                flash('Message sent successfully!', 'success')
            except Exception as e:
                flash(f'Failed to send message: {str(e)}', 'danger')

        # Fetch selected contacts from the database
        elif selected_contact_ids:
            selected_contacts = Contact.query.filter(Contact.id.in_(selected_contact_ids)).all()

            try:
                # Iterate through selected contacts and send messages
                for contact in selected_contacts:
                    # Implement Twilio message sending here for each contact

                    existing_conversation = Conversation.query.filter(
                        text("conversations.sender_number = :sender_number AND conversations.receiver_number = :receiver_number")
                    ).params(
                        sender_number=TWILIO_PHONE_NUMBER,
                        receiver_number="+1" + str(contact.number),
                    ).first()
                    # print(TWILIO_PHONE_NUMBER)
                    print(str(contact.number))

                    if existing_conversation:
                        conversation_id = existing_conversation.id
                        print("Using existing conversation")
                    else:
                        print("Creating new conversation")
                        new_conversation = Conversation(
                            sender_number=TWILIO_PHONE_NUMBER,
                            receiver_number="+1"+str(contact.number),
                            user_id=current_user.id,
                            contact_id=contact.id
                        )
                        db.session.add(new_conversation)
                        db.session.commit()
                        conversation_id = new_conversation.id

                    sender_user_id=current_user.id
                    print("Sender_User_ID:", sender_user_id)

                    new_message = Message(
                        content=message_body,
                        conversation_id=conversation_id,
                        sender_id=sender_user_id,
                        receiver_number="+1" + str(contact.number),
                        timestamp=datetime.now(),
                    )

                    db.session.add(new_message)

                    try:
                        twilio_client.messages.create(
                            body=message_body,
                            from_=TWILIO_PHONE_NUMBER,  # Your Twilio phone number
                            to=contact.number  # Use the contact's phone number
                        )
                    except Exception as e:
                        flash(f'Failed to send messages to contacts: {str(e)}', 'danger')

                db.session.commit()
                flash('Messages sent successfully!', 'success')
            except Exception as e:
                flash(f'Failed to send messages to contacts: {str(e)}', 'danger')

            return redirect(url_for('dashboard'))

    return render_template('dashboard.html', contacts=selected_contacts, form=form)

@app.route('/create_message', methods=['POST'])
def create_message():
    if request.method == 'POST':

        user_timezone = pytz.timezone(request.form.get('user_timezone', 'America/Los_Angeles'))

        # Create a timestamp with the correct timezone
        current_time = datetime.now(pytz.timezone(user_timezone))
        print("Current Time:", current_time)

        # Create a new message and assign the timestamp
        message = Message(content=request.form.get('message_content'), timestamp=current_time)

        # Store the message in your database
        db.session.add(message)
        db.session.commit()

        # Redirect or render a response as needed
        return redirect(url_for('some_other_route'))

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

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    unread_message_count = 0

    user_contacts = current_user.contacts
    form = DashboardForm()

    return render_template('dashboard.html', contacts=user_contacts, form=form, unread_message_count=unread_message_count)

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

##########Receiving Messages##########

# @app.route('/inbox', methods=['GET', 'POST'])
# @login_required
# def inbox():
#     if 'unread_message_count' in session:
#         unread_message_count = session['unread_message_count']
#     else:
#         unread_message_count = 0

#     # Retrieve the user's conversations from the database

#     user_conversations = Conversation.query.filter_by(user_id=current_user.id).all()

#     # Retrieve additional data (e.g., contact names and last message snippets)
#     conversations_data = []
#     for conversation in user_conversations:
#         contact_name = get_contact_name(conversation.contact_id)
#         last_message_snippet = get_last_message_snippet(conversation.id)
#         messages = Message.query.filter_by(conversation_id=conversation.id).all()

#         conversations_data.append({
#             'conversation': conversation,
#             'contact_name': contact_name,
#             'last_message_snippet': last_message_snippet,
#             'messages': messages
#         })
#     session['unread_message_count']= 0
#     session.modified = True

#     return render_template('inbox.html', conversations_data=conversations_data, unread_message_count=unread_message_count)
@app.route('/receive_message', methods=['POST'])
def receive_message():
    # Get the message details from the incoming request
    message_data = request.form  # Adjust this to your actual request data format

    # Your code to process and save the message in the database
    # ...

    # Increment the unread_message_count
    if 'unread_message_count' in session:
        session['unread_message_count'] += 1
    else:
        session['unread_message_count'] = 1

    # Mark the message as unread in your database
    # Assuming you have a Message model and use SQLAlchemy
    new_message = Message(
        sender_number=message_data['sender_number'],
        receiver_number=TWILIO_PHONE_NUMBER,
        content=message_data['content'],
        messages_read=False
    )
    db.session.add(new_message)
    db.session.commit()

    return 'Message received and processed'

@app.route('/inbox', methods=['GET', 'POST'])
@login_required
def inbox():
    conversations_data = []

    # Check if the inbox was accessed and set the message count
    if 'inbox_accessed' not in session:
        session['inbox_accessed'] = True
        session['unread_message_count'] = 0

        # Retrieve the user's conversations from the database
    user_conversations = Conversation.query.filter_by(user_id=current_user.id).all()

        # Retrieve additional data (e.g., contact names and last message snippets)
    for conversation in user_conversations:
        contact_name = get_contact_name(conversation.contact_id)
        last_message_snippet = get_last_message_snippet(conversation.id)
        # messages = Message.query.filter_by(conversation_id=conversation.id).all()
        messages = conversation.messages

        conversations_data.append({
            'conversation': conversation,
            'contact_name': contact_name,
            'last_message_snippet': last_message_snippet,
            'messages': messages
        })

        # Set the initial message count
    unread_message_count = session.get('unread_message_count', 0)
    # else:
    #     # Don't reset the message count
    #     unread_message_count = session.get('unread_message_count', 0)

    return render_template('inbox.html', conversations_data=conversations_data, unread_message_count=unread_message_count)

def get_contact_name(contact_id):
    contact = Contact.query.get(contact_id)
    if contact:
        contact_name = f"{contact.first_name} {contact.last_name}"
        print("Contact Name:", contact_name)
        return contact_name
    else:
        return "Unknown Contact"

def get_last_message_snippet(conversation_id):
    last_message = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.id.desc()).first()
    if last_message:
        return last_message.content[:50]  # Return the first 50 characters of the message content
    else:
        return "No Messages"

@app.route('/conversation/<int:conversation_id>')
@login_required
def view_conversation(conversation_id):
    # Retrieve the conversation and its messages
    conversation = Conversation.query.get_or_404(conversation_id)
    messages = conversation.messages
    contact_name = get_contact_name(conversation.contact_id)
    for message in conversation.messages:
        message.messages_read = True
    db.session.commit()
    return render_template('conversation.html', conversation=conversation, messages=messages, contact_name=contact_name)

def obtain_conversation_id(sender_number, receiver_number, user_id, contact_id):
    conversation = Conversation.query.filter_by(sender_number=sender_number, receiver_number=receiver_number).first() or Conversation.query.filter_by(sender_number=receiver_number, receiver_number=sender_number).first()
    if conversation:
        # Check if the conversation exists
        if not conversation.messages_read:
            conversation.messages_read = True  # Mark the conversation as read
            db.session.commit()
        return conversation.id
    else:
        # Create a new conversation if it doesn't exist and return its ID
        new_conversation = Conversation(sender_number=sender_number, receiver_number=receiver_number, user_id=user_id, contact_id=contact_id, messages_read=True)  # Mark the new conversation as read
        db.session.add(new_conversation)
        db.session.commit()
        return new_conversation.id

def csrf_exempt(view):
    @wraps(view)
    def decorated(*args, **kwargs):
        if request.path == '/incoming_sms':
            return view(*args, **kwargs)
        if not request.csrf_valid:
            abort(400)  # Return an error response if CSRF token is missing or invalid
        return view(*args, **kwargs)
    return decorated

@app.before_request
def disable_csrf():
    if request.path == '/incoming_sms':
        # Disable CSRF protection for the /incoming_sms route
        request.csrf_exempt = True

def get_user_id(sender_number):
    association = TwilioNumberAssociation.query.filter_by(twilio_number=sender_number).first()
    if association:
        return association.user_id
    return None

def get_contact_id(sender_number):
    contact = Contact.query.filter_by(number=sender_number).first()
    if contact:
        return contact.id
    return None

@app.route('/incoming_sms', methods=['POST'])
@csrf_exempt
def incoming_sms():
    if request.method == 'POST':
        print("Incoming SMS route is triggered")

    message_body = request.form.get('Body')
    print("Message Body:", message_body)

    sender_number = request.form.get('From')
    print("Sender Number:", sender_number)
    receiver_number = request.form.get('To')
    print("Receiver Number:", receiver_number)

    # Obtain the sender's information, conversation_id, and other necessary data
    sender_user_id = get_user_id(sender_number)
    print("Sender_User_ID:", sender_user_id)

    contact_id = get_contact_id(receiver_number)

    # You need to obtain the conversation_id here, whether from the request or elsewhere
    conversation_id = obtain_conversation_id(receiver_number, sender_number, sender_user_id, contact_id)

    # Set the receiver_number to the Twilio number
    receiver_number = TWILIO_PHONE_NUMBER

    # Create a new message with the obtained conversation_id
    new_message = Message(content=message_body, conversation_id=conversation_id, sender_id=sender_user_id, receiver_number=receiver_number)

    # Store the new message in the database
    db.session.add(new_message)
    db.session.commit()

    # After processing, you can redirect the user to their inbox or conversation
    return redirect(url_for('inbox'))

@app.route('/get_unread_message_count', methods=['GET'])
@login_required
def get_unread_message_count():
    # Check if the inbox was accessed and set the message count
    print("get_unread_message_count")
    print(session)
    if 'inbox_accessed' in session:
        session.pop('unread_message_count', None)
        session.pop('inbox_accessed', None)
        unread_message_count = 0

    unread_message_count = Message.query.filter(
        and_(Message.messages_read == False, Message.receiver_number == TWILIO_PHONE_NUMBER)
    ).count()

    app.config['unread_message_count'] = unread_message_count

    # Return the count as JSON
    return jsonify({'count': unread_message_count})


@app.route('/conversation/<int:conversation_id>/respond', methods=['GET', 'POST'])
@login_required
def respond_to_conversation(conversation_id):
    form = ResponseForm()

    if form.validate_on_submit():
        response = form.response.data

        # Retrieve the conversation and sender/receiver numbers
        conversation = Conversation.query.get_or_404(conversation_id)
        sender_number = conversation.sender_number
        receiver_number = conversation.receiver_number

        # Obtain the user_id and contact_id for the sender number
        user_id = get_user_id(sender_number)
        contact_id = get_contact_id(sender_number)

        # Create a new message with the obtained conversation_id
        new_message = Message(content=response, conversation_id=conversation_id)

        # Store the new message in the database
        db.session.add(new_message)
        db.session.commit()

        # Send the response to the receiver number using Twilio
        try:
            twilio_client.messages.create(
                body=response,
                from_=sender_number,
                to=receiver_number
            )
        except Exception as e:
            flash(f'Failed to send the response: {str(e)}', 'danger')

        flash('Response sent successfully!', 'success')

        # Redirect the user back to the conversation view
        return redirect(url_for('view_conversation', conversation_id=conversation_id))

    return render_template('response-form.html', form=form, conversation_id=conversation_id)

print("Before main block")
app.debug = True
if __name__ == '__main__':
    db.create_all()
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    app.run(debug=True, use_reloader=False, port=5000)
