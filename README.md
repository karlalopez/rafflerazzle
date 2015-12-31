# rafflerazzle

## WORK IN PROGRESS! :)

Please leave your comments and suggestions. Feedback and pull requests are very welcome.

This is a raffle manager.

Let's say you run a local meetup, and every meetup you raffle a prize to your participants. This app is supposed to help you keep track of your raffles and participants, using Twilio to handle the communication.

### How it works

The raffle home is in `/`. From there, participants find the number they have to text to enter the raffle.

The background image used on the raffle home is `/static/images/cover.png`. The one in the repo is from [WOCin Tech Chat](https://www.flickr.com/photos/wocintechchat) and it is free to use.

The Admin page is `/admin`.

### Some rules

* You can't delete a winner
* You can't delete a closed raffle
* You can't have 2 raffles at the same time.
* After a raffle is closed it will wait for you to draw a winner. You can do it from Admin home, Admin Raffles, or Raffle page.

### Improvements to come soon

* Download participants list in CSV
* Automaticly contact winner via text message
* Make it possible to automaticly draw winner when the raffle ends, if the Admin wants to.

## Running locally

For this app, you will need Mailgun and Twilio.

- Sign up for Mailgun free account at https://mailgun.com. You’ll need a few pieces of information from the Mailgun control panel before moving forward:

1. API Key
2. Sandbox Domain URL (should look like "sandboxc6235728hdkjehf283hajf13a90679.mailgun.org"
Both of these pieces of information can be found on the landing page of the Mailgun control panel.

- Sign up for [Twilio](https://www.twilio.com/try-twilio). Go to your [account page](https://www.twilio.com/user/account/phone-numbers/incoming) and get the phone number listed there.

Now that you have everything you need, we will keep your precious keys and number as environment variables. 

Your SECRET_KEY is not from any external service. It is like a password. Use any password you want.

- On Terminal:

```
$ export SECRET_KEY="YOUR_SECRETKEY"
$ export MAILGUN_SANDBOX_DOMAIN_URL="YOUR_SANDBOX_URL"
$ export MAILGUN_API_KEY="YOUR_API_KEY"
$ export TWILIO_NUMBER="+55555555555"
```
Note that the "export" is limited to the Terminal window you have open. You have to re-export every time you open a new window. (If this gets frustrating, see if you can figure out [autoenv.](https://github.com/kennethreitz/autoenv))

- Install Postgres:
Mac - http://postgresapp.com/
Windows - http://www.postgresql.org/download/windows/
Ubuntu - 'apt-get install postgresql'.

- On Terminal, start psql typing:

```
$ psql
```
- Now create the database:
```
create database raffle;
```
- To exit postgres just type:
```
\q
```

- Run the following code to install required dependencies:

```$ sudo pip install -r requirements.txt```


- Run `create_models.py` on Terminal, to create the tables in the database:

```$ python create_models.py```

It will ask you for your email to create the first Admin user. Copy the *temporary password* given. You will need that to login and have access to `/admin`

- Uncomment those 2 lines before you move forward.

- Run `app.py` and go to http://127.0.0.1/login to change your password.

You're good to go.

In case you want to populate the database with some data to make testing easier,
 you can run `populate.py`.

 ```$ python populate.py```

 It will create an active, a closed, and an upcoming raffle. All of them with 50 bogus participants.

* IMPORTANT:* To send and receive text messages, the app needs to be on server exposed to the public Internet, so Twilio can find it. Please find below instructions to do it using Heroku.

## Deploying it to Heroku 

- First, create a Heroku account: https://signup.heroku.com/

- Install the Heroku Toolbelt: https://toolbelt.heroku.com/

- Login to Heroku on Terminal:

```
$ heroku login
Enter your Heroku credentials.
Email: your@email.com
Password:
Authentication successful.
```

- Create the app, along with a git remote that must be used to receive your application source:

```$ heroku apps:create your_app_name```

Basically what happens here is that now you have one more remote git repo. If you list ou remote repos, you will see your Github and your Heroku repos:

```$ git remote -v```

Now every time you push something to Github with `git push`, you will have to push again to Heroku with `git push heroku` if you want it deployed. You can setup a [Github/Heroku integration](https://devcenter.heroku.com/articles/github-integration) if you want to automate this process.

- First things first, let's keep your keys and number as environment variables, this time at Heroku:

```
$ heroku config:add SECRET_KEY="YOUR_SECRET_KEY"
$ heroku config:set MAILGUN_SANDBOX_DOMAIN_URL="YOUR_SANDBOX_URL"
$ heroku config:set MAILGUN_API_KEY="YOUR_API_KEY"
$ heroku config:set TWILIO_NUMBER="+55555555555"
```

- Now let's set your [timezone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones):

```$ heroku config:add TZ="YOUR_TIME_ZONE"```

This is important because the raffles are time based. If you don't set it right, they won't work as expected.

Now, enable the PostgreSQL addon. This level is free but does have size and speed limitations (more details). https://elements.heroku.com/addons/heroku-postgresql

```$ heroku addons:create heroku-postgresql:hobby-dev```

When you've done this you should notice that it sets a variable on Heroku called DATABASE_URL. Check with heroku config. 

```$ heroku config```

This variable is in `app.py`:

```
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://localhost/raffle')
db = SQLAlchemy(app)
```

It means that when you run `app.py` locally, it will look for DATABASE_URL, fail, then look for the database on localhost.

- Let's get this code to Heroku:

```
$ git push heroku
```

The response will look like this:

```
Counting objects: 4, done.
Delta compression using up to 4 threads.
Compressing objects: 100% (4/4), done.
Writing objects: 100% (4/4), 373 bytes | 0 bytes/s, done.
Total 4 (delta 3), reused 0 (delta 0)
remote: Compressing source files... done.
remote: Building source:
remote:
remote: -----> Using set buildpack heroku/python
remote: -----> Python app detected
remote: -----> Installing dependencies with pip
remote:
remote:
remote: -----> Discovering process types
remote:        Procfile declares types -> web
remote:
remote: -----> Compressing... done, 41.4MB
remote: -----> Launching... done, v18
remote:        https://your_app_name.herokuapp.com/ deployed to Heroku
remote:
remote: Verifying deploy... done.
```

https://your_app_name.herokuapp.com/ is your URL. But you're still have need to create te tables.

- Run `create_models.py` to create the tables in the database on Heroku:

```$ heroku run python create_models.py```

Same thing: It will ask you for your email to create the first Admin user. Copy the *temporary password* given. You will need that to login and have access to `/admin`.


Now you're good to go: https://your_app_name.herokuapp.com/login

If you want to populate the database: 

```$ heroku run python populate.py```

Happy raffles!


Special thanks to Jennie Lees. Good chuncks of this documentation have been written based on her tutorials. Visit her portfolio: http://jennielees.github.io.


