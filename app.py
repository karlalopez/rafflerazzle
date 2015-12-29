from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, current_user
import os
from itsdangerous import URLSafeTimedSerializer
import sys
import logging

# Enter here your site name and tagline
site_name = "Rafflerazzle"
site_tagline = "Win! Win! Win!"

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

app.secret_key = 'SECRET_KEY'
ts = URLSafeTimedSerializer(app.config['SECRET_KEY'])

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://localhost/raffle')
db = SQLAlchemy(app)


# "InvalidRequestError: Table 'users' is already defined for this MetaData instance. 
# Specify 'extend_existing=True'", 
# If modules.py gives you this error above, comment the two lines below and try again.
from views import *
del session

if __name__ == "__main__":
    app.run(debug=True)
