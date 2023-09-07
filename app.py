from sqlite3 import IntegrityError
from flask import Flask, render_template, request, redirect, session, flash, g, url_for
from random import choice
import os
from forms import UserAddForm, LoginForm, ContactAddForm, EditForm
from models import db, connect_db, User, Contacts
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from flask_debugtoolbar import DebugToolbarExtension

CURR_USER_KEY = "curr_user"

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', 'postgresql:///greetings'))
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True

app.config['SECRET_KEY'] = 'salutations'

connect_db(app)
app.app_context().push()

debug = DebugToolbarExtension(app)

account_sid = os.environ.get('ACCOUNT_SID')
auth_token = os.environ.get('AUTH_TOKEN')
client = Client(account_sid, auth_token)

@app.route('/')
def home_page():

    form = LoginForm()
    message = request.args.get('message', '')

    if(g.user):
        contacts = Contacts.query.filter_by(username=g.user.username).all()
        return render_template("base.html", contacts=contacts, message=message)
    else:
        return render_template("users/login.html", form=form, message=message)


INQUIRIES = ["Are you sure you want to send this message?", "Is that all you want to say?", "Anything else?"]

@app.before_request
def user_auth():
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id

def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                password=form.password.data,
                email=form.email.data,
            )
            db.session.add(user)
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)

@app.route('/login', methods=["POST", "GET"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)
        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        else:
            flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)

@app.route('/contacts', methods=["POST", "GET"])
def add_contact():
    """Form to add contacts"""
    form = ContactAddForm()

    if form.validate_on_submit():
        # Retrieve the submitted data from the form
        user_id = form.username.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        number = form.number.data

        # Retrieve the hidden number from the form data
        hidden_number = request.form['hidden_number']

        try:
            contact = Contacts(
                user_id=g.user.username,
                first_name=first_name,
                last_name=last_name,
                number=number,
                hidden_number=hidden_number
            )
            db.session.add(contact)
            db.session.commit()

            contacts = Contacts.query.filter_by(user_id=g.user.username).all()

            flash("Contact added successfully!", "success")
            return render_template("users/add_contacts.html", form=form, contacts=contacts)

        except IntegrityError:
            flash("Contact already added!", "danger")
            return render_template("users/add_contacts.html", form=form)

    else:
        contacts = Contacts.query.filter_by(username=g.user.username).all()
        return render_template("users/add_contacts.html", contacts=contacts, form=form)

@app.route('/contacts/<int:contact_id>/update', methods=['GET', 'POST'])
def edit_contact(contact_id):
    contact = Contacts.query.get(contact_id)
    form = ContactAddForm(obj=contact)

    if form.validate_on_submit():
        form.populate_obj(contact)
        db.session.commit()
        flash('Contact updated successfully!', 'success')
        return redirect('/contacts')

    return render_template('users/edit_contact.html', form=form, contact=contact)

@app.route('/contacts/<int:contact_id>/delete', methods=['POST'])
def delete_contact(contact_id):
    contact = Contacts.query.get(contact_id)
    if contact:
        db.session.delete(contact)
        db.session.commit()
        flash('Contact deleted successfully!', 'success')
    else:
        flash('Contact not found', 'error')

    return redirect('/contacts')

@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    flash("You have successfully logged out")

    return redirect('/login')

@app.route('/edit', methods=['GET', 'POST'])
def edit_message():
    form = EditForm()

    if request.method == 'POST':
        message = request.form['message']
        recipient_name = request.form['recipient']

        contact = Contacts.query.filter_by(username=g.user.username, first_name=recipient_name).first()
        if contact:
            recipient_number = contact.number
            # Send the message to the recipient_number
            # ...
            try:
                client.messages.create(
                    body=message,
                    from_='+18777649862',
                    to=recipient_number
                )
            except TwilioRestException as e:
                print(f"Twilio Error: {str(e)}")
            verify = choice(INQUIRIES)
            return render_template('edit.html', form=form, verify=verify, message=message, recipient=recipient_name)
        else:
            # Handle the case when the recipient name is not found
            flash("Recipient name not found.", "danger")
            return render_template('edit.html', form=form)
    else:
        message = request.args.get('message', '')
        recipient = request.args.get('recipient', '')
        verify = choice(INQUIRIES)
        return render_template('edit.html', form=form, message=message, recipient=recipient)

@app.route('/send', methods=['GET', 'POST'])
def send():
    if request.method == 'POST' and 'submit' in request.form:
        message = request.form['message']
        recipients = request.form.getlist('recipients[]')
        print(message)
        print(recipients)
        print(recipients, '++++')

        if recipients:
            print(recipients)

            for recipient in recipients:
                print(recipient, "$$$$")
                client.messages.create(
                    body=message,
                    from_='+18777649862',
                    to=recipient
                )

            return render_template("success.html", message=message, recipients=recipients)
    else:
        return redirect('/')
