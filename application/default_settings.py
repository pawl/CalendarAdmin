import os
from authomatic.providers import oauth2, oauth1
from application.auth_providers import Eventbrite

# Get application base dir.
_basedir = os.path.abspath(os.path.dirname(__file__))

STATIC_ROOT = 'static'
SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
SQLALCHEMY_ECHO = False
MANDRILL_API_KEY = os.environ['MANDRILL_API_KEY']
MANDRILL_DEFAULT_FROM = 'admin@calendaradmin.com'
SECRET_KEY = os.environ['SECRET_KEY']
PORT = 80
IMGUR_ID = os.environ['IMGUR_ID']
DOMAIN_NAME = os.environ['DOMAIN_NAME'] + ":" + str(PORT)
DEBUG = True
RELOAD = True
CSRF_ENABLED = True
ENCRYPTION_KEY = os.environ['ENCRYPTION_KEY']

AUTH = {
    'google': {
        'class_': oauth2.Google,
        'consumer_key': os.environ['GOOGLE_CUSTOMER_KEY'],
        'consumer_secret': os.environ['GOOGLE_CUSTOMER_SECRET'],
        'id': 1,
        'scope': ['https://www.googleapis.com/auth/userinfo.profile',
                  'https://www.googleapis.com/auth/userinfo.email',
                  'https://www.googleapis.com/auth/calendar'],
    },
    'meetup': {
        'class_': oauth1.Meetup,
        'consumer_key': os.environ['MEETUP_CUSTOMER_KEY'],
        'consumer_secret': os.environ['MEETUP_CUSTOMER_SECRET'],
        'id': 2,
    },
    'eventbrite': {
        'class_': Eventbrite,
        'consumer_key': os.environ['EVENTBRITE_CUSTOMER_KEY'],
        'consumer_secret': os.environ['EVENTBRITE_CUSTOMER_SECRET'],
        'id': 3,
    },
}
