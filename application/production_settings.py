import os

from authomatic.providers import oauth2, oauth1
import authomatic

# Get application base dir.
_basedir = os.path.abspath(os.path.dirname(__file__))

STATIC_ROOT = 'static'
SQLALCHEMY_ECHO = False
SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
MANDRILL_API_KEY = os.environ['MANDRILL_API_KEY']
MANDRILL_DEFAULT_FROM = 'admin@calendaradmin.com'
SECRET_KEY = os.environ['SECRET_KEY']
DOMAIN_NAME = os.environ['DOMAIN_NAME']
PORT = 80
DEBUG = False
RELOAD = False
CSRF_ENABLED = True
ENCRYPTION_KEY = os.environ['ENCRYPTION_KEY']

AUTH = {
	'google': {
		'class_': oauth2.Google,
		'consumer_key': os.environ['GOOGLE_CUSTOMER_KEY'],
		'consumer_secret': os.environ['GOOGLE_CUSTOMER_SECRET'],
		'id': 1,
		'scope': ['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/calendar'],
	},
	'meetup': {
		'class_': oauth1.Meetup,
		'consumer_key': os.environ['MEETUP_CUSTOMER_KEY'],
		'consumer_secret': os.environ['MEETUP_CUSTOMER_SECRET'],
		'id': 2,
	},
}
