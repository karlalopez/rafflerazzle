from flask import render_template, request, redirect, session, jsonify, url_for, stream_with_context, abort
from app import *
from models import *
from forms import *
from datetime import date
from datetime import timedelta
from io import BytesIO
from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response
import csv
import time
import twilio.twiml

login_manager = LoginManager()
login_manager.init_app(app)

def redirect_url(default='index'):
# helper function to understand requests context: http://flask.pocoo.org/docs/0.10/reqcontext/  
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)

# User handling based on https://exploreflask.com/users.html

@login_manager.user_loader
# Load admin user
def load_user(userid):
    return User.query.filter(User.id==userid).first()

@app.route('/login', methods=['GET', 'POST'])
# Admin user login
def login():
    # Load the login form
    form = LoginForm(request.form)
    # To login admin user
    if request.method == 'POST' and form.validate():
        # Check password
        user = get_user_by_email(form.email.data)
        if user and user.is_correct_password(form.password.data):
            # Login admin user
            login_user(user)            
            return redirect('/admin')
    	else:
        	return render_template('login.html', error="Login credentials don't not work", form=form, site_name=site_name)
    return render_template('login.html', form=form, site_name=site_name)

@app.route('/logout')
# Admin user logout
def logout():
    if current_user.is_authenticated():
        # Logout user
        logout_user()
    return redirect('/login')


@app.route('/forgot', methods=['GET', 'POST'])
# Request password reset for admin user
def forgot():
    if current_user.is_authenticated():
        return redirect('/')

    # Load the Forgot password form
    form = ForgotPasswordForm(request.form)
    
    # To send reset password email ti user admin
    if request.method == 'POST' and form.validate():
        # Check if te user exists
        user = get_user_by_email(form.email.data)

        if user:
            # If the user exists, put together the reset password link and email body
            subject = "{} - Have you requested a password reset?".format(site_name)

            token = ts.dumps(form.email.data, salt='recover-key')

            reset_url = url_for(
                'reset',
                token=token,
                _external=True)

            html = render_template(
                'email-reset.html',
                reset_url=reset_url, site_name=site_name)

            # Send email
            send_email_to_user(form.email.data, subject, html)
        
        # For security reasons, it does not confirm if the email is or is not in the db
        message = "Please follow the instructions sent to {} to reset your password.".format(form.email.data)
        return render_template('forgot.html', message=message, form=form, site_name=site_name)
        
    return render_template('forgot.html', form=form, site_name=site_name)

@app.route('/confirm/<token>')
# Admin user email confirmation
def confirm_email(token):
    # Load the login form
    form = LoginForm(request.form)
    try:
        # Get the email out of the token in the URL
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
    except:
        return render_template('login.html', error="Your user could not be confirmed. Please contact us.", form=form, site_name=site_name)

    # Perform the email confirmation
    confirmation = confirm_user(email)
    if confirmation:

    	# If the user is confirmed, put together the set password link and email body
        subject = "{} - Let's set your password".format(site_name)

        token = ts.dumps(email, salt='recover-key')

        reset_url = url_for(
            'reset',
            token=token,
            _external=True)

        html = render_template(
            'email-set.html',
            reset_url=reset_url, site_name=site_name)

        # Send email
        send_email_to_user(email, subject, html)

        message = "Your user is now confirmed. Follow the instructions sent to {} and set your password.".format(email)

        return render_template('login.html', message=message, form=form, site_name=site_name)
    else:
        return render_template('login.html', error="Your user could not be confirmed. Please contact us.", form=form, site_name=site_name)

@app.route('/reset/<token>', methods=['GET', 'POST'])
# Reset admin user password
def reset(token):
    try:
        # Get the email out of the token in the URL and validate
        email = ts.loads(token, salt="recover-key", max_age=86400)
    except:
        # Redirect to 404 if no user binded to token
        return redirect('/404')
    
    form = ResetPasswordForm(request.form)

    # To validate password reset
    if request.method == 'POST':
        if form.validate():
            # If form validates, retrieve the user
            user = get_user_by_email(email)
            # Change password to new password
            reset_confirmation = change_user_password(user, form.new_password.data)
            if reset_confirmation:
                # If password change goes well, send user to login
                form = LoginForm(request.form)
                return render_template('login.html', message="Your password has been changed. Please login in here.", form=form, site_name=site_name)
            else:
                # If password change does not go well, send user to login and asks for contact.
                form = LoginForm(request.form)
                return render_template('login.html', error="Your password reset did not work. Please contact us.", form=form, site_name=site_name)
        else:
            # Tell the user to match password fields
            return render_template('reset.html', token=token, error="Your new password must match the confimed password field.", form=form, site_name=site_name)
    # If GET, load the reset password form
    return render_template('reset.html', token=token, form=form, site_name=site_name)    


@app.route('/')
# Raffle main page - to participants
def index():
    print now
    active_raffle = get_active_raffle()
    return render_template('index.html', twilio_number=TWILIO_NUMBER, active_raffle=active_raffle,site_name=site_name)

@app.route('/admin')
# User admin main page
def admin():
    if current_user.is_authenticated():
        participants = get_participants_last_10()
        upcoming_raffles = get_upcoming_raffles()
        closed_raffles = get_closed_raffles()
        raffle_winners = get_raffles_with_winners()
        participants_number = False

        raffle = get_active_raffle()
        # If there's an active raffle, count the number of participants in the raffle
        if raffle:
            participants_number = count_participants_by_raffle(raffle.id)
    
        return render_template('admin.html', raffle=raffle, raffle_winners=raffle_winners, participants_number=participants_number,closed_raffles=closed_raffles,upcoming_raffles=upcoming_raffles, participants=participants, site_name=site_name)	
    
    else:
        return redirect('/login')
		
@app.route('/admin/profile', methods=['GET', 'POST'])
# Admin user profile, password change
def profile():
    if current_user.is_authenticated():

        # Load the password change form    
        form = ChangePasswordForm(request.form)

        # To change password
        if request.method == 'POST' and form.validate():
            user = get_user_by_email(current_user.email)
            # Validates old password
            if user.is_correct_password(form.old_password.data):
                # Changes user password to new_password
                try:
                    change_user_password(current_user, form.new_password.data)
                    return render_template('profile.html', form=form, site_name=site_name, message="Your password has been changed successfuly.")
                except Exception as e:
                    return render_template('profile.html', form=form, site_name=site_name, error=e.message)
            else:
                return render_template('profile.html', form=form, site_name=site_name, error="Password does not match")

        return render_template('profile.html', form=form, site_name=site_name)
    else:
        return redirect('/login')

@app.route('/admin/users', methods=['GET', 'POST'])
# Admin user management
def admin_users():
    if current_user.is_authenticated():

        # Load the add user form    
        form = AddUserForm(request.form)
        
        # To create a new admin user
        if request.method == 'POST' and form.validate():
            email = form.email.data
            user = get_user_by_email(email)
            # Check if the admin user is already in the database
            if not user:
                password = pass_generator()
                # Create admin user
                create_user(email, password)
                # Send email confirmation
                send_email_confirmation(email)
                error=None
            else:
                # If the admin user is already in the database, show error message
                users = get_users()
                error = "User already in the database."
                return render_template('admin-users.html', error=error, form=form, site_name=site_name, users=users)
        
        users = get_users()
        return render_template('admin-users.html', form=form, site_name=site_name, users=users)
    
    else:
		return redirect('/login')

@app.route('/admin/user-delete/<user_id>')
# Delete admin user
def admin_users_delete(user_id):
    if current_user.is_authenticated():
 
        user = get_user_by_id(user_id) 
        # Check if the admin user exists before deleting it     
        if user:
            # Delete admin user
            delete_user(user.id)
        return redirect('/admin/users')
    
    else:
        return redirect('/login')


@app.route('/admin/participants')
# Participant management
def admin_participants():
    if current_user.is_authenticated():

        winners = get_winners()
        participants = get_participants()
        return render_template('admin-participants.html', winners=winners, site_name=site_name, participants=participants)
    
    else:
        return redirect('/login')

@app.route('/admin/participant-delete/<participant_id>')
# Delete participant
def admin_participant_delete(participant_id):
    if current_user.is_authenticated():

        winner = get_winner_by_participant_id(participant_id)
        # Check if the participant is already a winner. (You can not delete a winner)
        if winner:
            return redirect('/admin/error?delete-participant')

        # If the participant is not a winner, delete participant
        participant = get_participant_by_id(participant_id)
        if participant:
            delete_participant(participant.id)
        return redirect('/admin/participants')

    else:
        return redirect('/login')

@app.route('/admin/raffles', methods=['GET', 'POST'])
# Raffle management
def admin_raffles():
    if current_user.is_authenticated():

        raffles = get_raffles()
        raffle_winners = get_raffles_with_winners()

        # Show raffles list
        if request.method == 'GET':
            return render_template('admin-raffles.html', raffle_winners=raffle_winners,site_name=site_name, raffles=raffles, now=now)

        # To create a new raffle
        prize = request.form.get('raffle_prize')
        start = request.form.get('raffle_dt_start')
        end = request.form.get('raffle_dt_end')

        dt_start = datetime.strptime(start, "%m/%d/%Y %I:%M %p").strftime("%Y-%m-%d %H:%M:%S")
        dt_end = datetime.strptime(end, "%m/%d/%Y %I:%M %p").strftime("%Y-%m-%d %H:%M:%S")

        # Check if the dates conflict with an existent raffle
        if check_for_raffle_conflict(False,dt_end):
            error = "Sorry! A new raffle can not conflict with existent raffles."
            return render_template('admin-raffles.html', error=error, raffle_winners=raffle_winners,site_name=site_name, raffles=raffles, now=now)

        # If it does not, create raffle
        raffle = create_raffle(prize, dt_start, dt_end)
        if raffle:
            raffles = get_raffles()
            return render_template('admin-raffles.html', site_name=site_name, raffle_winners=raffle_winners,raffles=raffles, now=now)
        # If there's an error creating the raffle, show error message
        else:
            error = "Raffle could not be created."
            return render_template('admin-raffles.html', error=error, site_name=site_name, raffles=raffles, now=now)
    
    else:
        return redirect('/login')

@app.route('/admin/raffle/delete/<raffle_id>')
# Delete raffle
def admin_raffle_delete(raffle_id):
    if current_user.is_authenticated():

        raffle = get_raffle_by_id(raffle_id) 
        # Check is raffle is closed. (You can't delete closed raffles)     
        if raffle.dt_end > now:
            delete_raffle(raffle.id)
            return redirect('/admin/raffles')
        else:
        # If raffle is closed, show error message    
            return redirect('/admin/error?delete-raffle')
    
    else:
        return redirect('/login')

@app.route('/admin/raffle/<raffle_id>', methods=['GET', 'POST'])
def admin_raffle_edit(raffle_id):
# Update a raffle    
    if current_user.is_authenticated():

        raffle = get_raffle_by_id(raffle_id)
        participants = get_participants_by_raffle(raffle_id)
        winner = get_winner_by_raffle(raffle_id)
        
        # If the raffle already has a winner, get winner's contact
        if winner:
            winner_contact = get_participant_by_id(winner.participant_id)
        else:
            winner_contact = False
        
        if request.method == 'GET':
            return render_template('admin-raffles-edit.html', winner_contact=winner_contact, site_name=site_name, raffle=raffle, participants=participants, now=now, winner=winner)
        
        # To update a winner
        prize = request.form.get('raffle_prize')
        start = request.form.get('raffle_dt_start')
        end = request.form.get('raffle_dt_end')

        dt_start = datetime.strptime(start, "%m/%d/%Y %I:%M %p").strftime("%Y-%m-%d %H:%M:%S")
        dt_end = datetime.strptime(end, "%m/%d/%Y %I:%M %p").strftime("%Y-%m-%d %H:%M:%S")

        # Check for conflict raffle dates
        if check_for_raffle_conflict(raffle,dt_end):

            error = "Sorry! A new raffle can not conflict with existent raffles."
            return render_template('admin-raffles-edit.html', winner_contact=winner_contact, error=error, site_name=site_name, raffle=raffle, participants=participants, now=now, winner=winner)
        
        # If no conflict, update rafle
        updated_raffle = update_raffle(raffle, prize, dt_start, dt_end)

        # If update goes well
        if updated_raffle:
            return redirect('/admin/raffles')
        # If it does't go well, show error message            
        else:
            error = "Raffle could not be updated."
            return render_template('admin-raffles-edit.html', winner_contact=winner_contact, error=error, site_name=site_name, raffle=raffle, participants=participants, now=now)
    
    else:
        return redirect('/login')

@app.route('/admin/draw/<raffle_id>', methods=['POST'])
# Draw raffle winner
def draw_winner(raffle_id):
    if current_user.is_authenticated():
        
        closed_raffles = get_closed_raffles()
        raffle = get_raffle_by_id(raffle_id)
        
        # Make sure the raffle is closed
        if raffle in closed_raffles:
            # Draw winner
            winner = draw_raffle_winner(raffle_id)
            # If it goes well
            if winner:
                return redirect(redirect_url())

        # If does not go well, show error message 

        participants = get_participants_last_10()
        upcoming_raffles = get_upcoming_raffles()
        raffle_winners = get_raffles_with_winners()
        participants_number = False
        raffle = get_active_raffle()
        error = "Sorry! Couldn't draw a winner for this raffle. Please check if the raffle has participants or if there is a winner already."
        return render_template('admin.html', error=error, raffle=raffle, raffle_winners=raffle_winners, participants_number=participants_number,closed_raffles=closed_raffles,upcoming_raffles=upcoming_raffles, participants=participants, site_name=site_name)  
    
    else:
        return redirect('/login')

@app.route('/admin/error')
# Generic error page
def admin_error():
    if current_user.is_authenticated():
        print request.query_string

        if request.query_string == "delete-raffle":
            error = "Can't delete raffles that have already finished."
        if request.query_string == "delete-participant":
            error = "Can't delete raffle winner."
        else:
            error = "Unkown"
        return render_template('admin-error.html', error=error, site_name=site_name)

    else:
        return redirect('/login')

@app.route("/hello_raffle", methods=['GET', 'POST'])
# Twilio handling: https://www.twilio.com/docs/quickstart/python/sms/replying-to-sms-messages     
def hello_raffle():       
            
    if request.method == 'POST':

        raffle = get_active_raffle()

        phone = request.values.get('From', None)
        resp = twilio.twiml.Response() 


        if raffle:
            participant = create_participant(phone, raffle.id)
            if participant:
                resp.message("Thanks, you're in the raffle!")
            else:
                resp.message("Sorry! Something wrong happened. You're are not in raffle.")
        else:
            resp.message("Sorry, no active raffles right now.")    

        return str(resp)
    return str("Hello, raffle monkey!")    


      
       
  
  



