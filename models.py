from app import app, db, site_name, site_tagline, ts
from sqlalchemy.ext.hybrid import hybrid_property
from flask.ext.bcrypt import Bcrypt
from sqlalchemy import func, and_
from sqlalchemy.sql import text
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask.ext.login import UserMixin, login_user, logout_user
from flask import render_template, url_for
import time
import json
import os
import requests
import string
import random
from datetime import *
import twilio.twiml


now = datetime.now()
nowiso = now.isoformat()

bcrypt = Bcrypt(app)
BCRYPT_LOG_ROUNDS = 12

MAILGUN_API_KEY = os.environ['MAILGUN_API_KEY']

MAILGUN_SANDBOX_DOMAIN_URL = os.environ['MAILGUN_SANDBOX_DOMAIN_URL']

TWILIO_NUMBER = os.environ['TWILIO_NUMBER']


# User Model
# Very simple. This is a Rafflerazzle admin user. Email, date created, password (stored with bcrypt) and email confirmation. 
# If the user does not confirm his or her email, password reset is not allowed.

class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100),unique=True)
    dt_created = db.Column(db.DateTime)
    _password = db.Column(db.String(100))
    email_confirmed = db.Column(db.Boolean)

    def __init__(self, email, dt_created, password):
        self.email = email
        self.dt_created = dt_created
        self.password = password
        self.email_confirmed = False

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        self._password = bcrypt.generate_password_hash(plaintext)

    def is_correct_password(self, plaintext):
        return bcrypt.check_password_hash(self._password, plaintext)


# User related functions
# User handling based on https://exploreflask.com/users.html

def get_users():
    # Get all users
    users = User.query.all()
    return users

def get_user_by_email(email):
    # Get user by email
    return User.query.filter_by(email=email).first()

def get_user_by_id(id):
    # Get user by user id
    return User.query.filter_by(id=id).first()


def create_user(email, password):
    # Create a new user
    dt_created = now
    user = User(email, dt_created, password)
    db.session.add(user)
    db.session.commit()
    return user

def send_email_confirmation(email):
    # Puts together email confirmation to user
    subject = "{} - Please confirm your email".format(site_name)       

    token = ts.dumps(email, salt='email-confirm-key')        

    confirm_url = url_for(     
        'confirm_email',       
        token=token,       
        _external=True)        

    html = render_template('email-confirmation.html', confirm_url=confirm_url, site_name=site_name, site_tagline=site_tagline)     

    # Send email       
    send_email_to_user(email, subject, html) 

def confirm_user(email):
    # Mark the user as email confirmed 
    user = get_user_by_email(email)
    if user:

        user.email_confirmed = True
        try:
            db.session.add(user)
            db.session.commit()
            return user
        except:
            db.session.rollback()

def change_user_password(user, user_password):
    # Change user password
    user.password = user_password
    try:
        db.session.commit()
        return user
    except:
        db.session.rollback()
        return False

def delete_user(id):
    # Check if the user exists
    user = get_user_by_id(id)
    if user:
        db.session.delete(user)
        # Delete user
        try:
            db.session.commit()
        except:
            db.session.rollback()

def pass_generator(size=12, chars=string.ascii_uppercase + string.digits):
    # Create a password for the very fisrt user
    return ''.join(random.choice(chars) for _ in range(size))

# Participant model
# This is the participant of the raffle. Date created, phone number & raffle id (foreig key to Raffle model)

class Participant(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    dt_created = db.Column(db.DateTime)
    phone = db.Column(db.String(100),unique=True)
    raffle_id = db.Column(db.Integer, db.ForeignKey('raffle.id'))
    raffle = db.relationship("Raffle", backref="participant")

    def __init__(self, phone, dt_created, raffle_id):
        self.dt_created = now
        self.phone = phone
        self.raffle_id = raffle_id

# Participant related functions

def get_participants():
    # Get all participants
    participants = Participant.query.all()
    return participants

def get_participants_by_raffle(raffle_id):
    # Get all participants from a particular raffle
    participants = Participant.query.filter_by(raffle_id=raffle_id).all()
    return participants

def count_participants_by_raffle(raffle_id):
    # Count number of participants from a particular raffle
    participants_number = Participant.query.filter_by(raffle_id=raffle_id).count()
    return participants_number

def get_participants_last_10():
    # Get last 10 participants to sign up to any raffle
    participants = Participant.query.limit(10)
    return participants

def get_participant_by_id(id):
    # Get participant by id
    return Participant.query.filter_by(id=id).first()

def create_participant(phone, raffle_id):
    # Create a new participant for a particular raffle
    dt_created = now
    participant = Participant(phone, dt_created, raffle_id)
    db.session.add(participant)
    db.session.commit()
    return participant

def delete_participant(id):
    # Checks if the participant exists
    participant = get_participant_by_id(id)
    if participant:
        db.session.delete(participant)
        # Deletes prticipant
        try:
            db.session.commit()
        except:
            db.session.rollback()


# Raffle model
# A raffle has a prize, a start date, and an end date.

class Raffle(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    prize = db.Column(db.String(200))
    dt_start = db.Column(db.DateTime)
    dt_end = db.Column(db.DateTime)

    def __init__(self, prize, dt_start, dt_end):
        self.prize = prize
        self.dt_start = dt_start
        self.dt_end = dt_end

# Raffle related functions

def get_active_raffle():
    # Get the on going raffle (hapenning right now)
    raffle = db.session.query(Raffle).\
               filter(and_(Raffle.dt_start <= now, 
                Raffle.dt_end >= now,)).\
                            first()
    if raffle:
        return raffle
    else:
        #If there's no active raffle, return False
        return False

def get_upcoming_raffles():
    # Get list of upcoming raffles
    raffles = db.session.query(Raffle).\
               filter(Raffle.dt_start > now).all()
    return raffles

def get_closed_raffles():
    # Get list of closed raffles
    raffles = db.session.query(Raffle).\
               filter(Raffle.dt_end < now).all()
    return raffles

def get_raffles():  
    # Get all raffles that ever happened
    raffles = Raffle.query.order_by(Raffle.dt_end.desc()).all()
    return raffles

def get_raffle_by_id(id):
    # Get raffle by id
    return Raffle.query.filter_by(id=id).first()

def create_raffle(prize, dt_start, dt_end):
    # Create new raffle  
    raffle = Raffle(prize, dt_start, dt_end)    
    try:
        db.session.add(raffle)
        db.session.commit()
        return raffle
    except:
        db.session.rollback()

def check_for_raffle_conflict(raffle_to_update, dt_end):
    # Check for conflicting dates in raffles
    end = datetime.strptime(dt_end,"%Y-%m-%d %H:%M:%S")
    raffles = db.session.query(Raffle).\
               filter(Raffle.dt_end >= end).all()
    if raffles:
        for raffle in raffles:
            if raffle.dt_start <= end:
                if raffle_to_update == raffle:
                    return False
                else:
                    return True
            else:
                return False
    else:
        return False

def update_raffle(raffle, prize, dt_start, dt_end):
    # Update raffle
    raffle.prize = prize
    raffle.dt_start = dt_start
    raffle.dt_end = dt_end
    try:
        db.session.commit()
        return raffle
    except:
        db.session.rollback()

def delete_raffle(id):
    # Check if the raffle exists
    raffle = get_raffle_by_id(id)
    if raffle:
        db.session.delete(raffle)
        # Delete user
        try:
            db.session.commit()
        except:
            db.session.rollback()

# Winner model
# The winner has a raffle id (foreign key to Raffle model), 
# a particpant id (the winner, foreign key to Participant model),
# and date created.

class Winner(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    raffle_id = db.Column(db.Integer, db.ForeignKey('raffle.id'))
    raffle = db.relationship("Raffle", backref="winner")    
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    participant = db.relationship("Participant", backref="winner")
    dt_created = db.Column(db.DateTime)

    def __init__(self, raffle_id, participant_id, dt_created):
        self.raffle_id = raffle_id
        self.participant_id = participant_id
        self.dt_created = dt_created

def get_winner_by_raffle(raffle_id):
    # Get the winner of a particular raffle
    return Winner.query.filter_by(raffle_id=raffle_id).first()

def get_winner_by_participant_id(participant_id):
    # Get winner by participant id, if you want to check is a particular participant is
    # or isn't a winner
    return Winner.query.filter_by(participant_id=participant_id).first()

def get_winners():
    # Create an array with ids of participants that have won raffles
    winners = Winner.query.all()
    participants = [None]
    for winner in winners:
        participants.append(winner.participant_id)
    return participants

def get_raffles_with_winners():
    # Get all raffles that already have winners
    winners = Winner.query.all()
    raffles = ["0"]
    for winner in winners:
        raffles.append(winner.raffle_id)
    return raffles

def draw_raffle_winner(raffle_id):
    # Check is this raffle already has a winner
    if get_winner_by_raffle(raffle_id):
        return False
  
    # If not, check if this raffle has participants
    participants = get_participants_by_raffle(raffle_id)    
    if participants:
        # If it does, draw winner
        draw = random.randint(0,(len(participants)-1))
        # Create a new winner
        winner = Winner(raffle_id, participants[draw].id, now)  
        try:
            db.session.add(winner)
            db.session.commit()
            return winner
        except:
            db.session.rollback()
    # If no participants, return False           
    return False


# General functions

def send_email_to_user(email, subject, html):
    # Send email
    mailgun_url = "https://api.mailgun.net/v3/{}/messages".format(MAILGUN_SANDBOX_DOMAIN_URL)
    from_site_name = "{} <mailgun@{}>".format(site_name, MAILGUN_SANDBOX_DOMAIN_URL)
    return requests.post(
        mailgun_url,
        auth=("api", MAILGUN_API_KEY),
        data={"from": from_site_name,
              "to": [email],
              "subject": subject,
              "text": html})

if __name__ == "__main__":
    # Run this file directly to create the database tables.
    print "Creating database tables..."
    db.create_all()
    print "Done!"
    users = get_users()
    if users:
        print "Your admins are:"
        for user in users:
            print user.email
    else:
        print "Enter your email:"
        email = raw_input().lower()
        password = pass_generator()
        create_user(email, password)
        confirm_user(email)
        print "Your user is: {}".format(email)
        print "Your password is {}:".format(password)
        print "PLEASE CHANGE YOUR PASSWORD ON YOUR FIRST LOGIN!!"

