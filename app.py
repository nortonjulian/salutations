from flask import Flask, render_template, request, redirect, session
from random import choice
import os
from twilio.rest import Client
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)

app.config['SECRET_KEY'] = 'salutations'
debug = DebugToolbarExtension(app)

account_sid = os.environ.get('ACCOUNT_SID')
auth_token = os.environ.get('AUTH_TOKEN')
client = Client(account_sid, auth_token)


@app.route('/')
def home_page():
    return render_template("home.html")

INQUIRIES = ["Are you sure you want to send this message?", "Is that all you want to say?", "Anything else?"]

@app.route('/edit', methods=['POST'])
def edit_message():

    verify = choice(INQUIRIES)
    return render_template('edit.html', verify=verify)

@app.route('/send', methods=['POST'])
def send():
    messages = request.form['message']
    recipients = request.form['recipient'].split(',')
    for recipient in recipients:
        client.messages.create(body=messages,
                               from_='+18777649862',
                               to=recipient)

    return render_template("success.html", messages=messages, recipients=recipients)
