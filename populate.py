from app import app, db, site_name, site_tagline, ts
import datetime
from time import sleep
from models import *

now = datetime.now()
nowiso = now.isoformat()
one_day = timedelta(days=1)

# creates participants for a raffle
def pp_create_participants(raffle_id):
	for i in range (0,50):
		participant_phone = "+{}".format(random.randint(12345678910,19876543210))
		partipant = create_participant(participant_phone, raffle_id)
	print "50 participats added per raffle."


# creates 3 raffles: active, closed and upcoming
def pp_create_raffles():
	# create 2 closed raffles:
	dt_start = datetime.now() - one_day
	dt_end = datetime.now()
	raffle = create_raffle("Prize closed raffle", dt_start, dt_end)
	print "Closed raffle added."
	sleep(5)
	# create 2 upcoming raffles:
	dt_start = datetime.now() + one_day + one_day
	dt_end = datetime.now() + one_day + one_day + one_day + one_day
	raffle = create_raffle("Prize upcoming raffle", dt_start, dt_end)
	print "Upcoming raffle added."
	sleep(5)
	# create an active raffle:
	dt_start = datetime.now()
	dt_end = datetime.now() + one_day
	raffle = create_raffle("Prize active raffle", dt_start, dt_end)
	print "Added raffle added."

if __name__ == "__main__":
	print "Populating..."
	pp_create_raffles()
	raffles = get_raffles()
	for raffle in raffles:
		pp_create_participants(raffle.id)
	print "Ready!"



