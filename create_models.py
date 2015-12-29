from app import db
from models import get_users

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

