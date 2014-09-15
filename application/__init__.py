import flask_wtf
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from authomatic import Authomatic
from flask.ext.login import LoginManager
from flask.ext.mandrill import Mandrill
from flask.ext.admin import Admin
from flask.ext.admin.menu import MenuLink

app = Flask(__name__)

db = SQLAlchemy(app)
app.config.from_object('application.default_settings')
app.config.from_envvar('PRODUCTION_SETTINGS', silent=True)

# log to papertrail in heroku
if not app.debug:
	import logging
	app.logger.addHandler(logging.StreamHandler())
	app.logger.setLevel(logging.INFO)

flask_wtf.CsrfProtect(app)

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

mandrill = Mandrill(app)

authomatic = Authomatic(app.config['AUTH'], app.config['SECRET_KEY'], report_errors=False)

from application.views import *	 
from application.hooks import *  

admin = Admin(app, "Calendar Admin", static_url_path="/assets", base_template='base.html', index_view=MyAdminIndexView(name='Home', template='home.html', url='/'), template_mode='bootstrap3')
admin.add_link(MenuLink(name='User Guide', url='https://docs.google.com/document/d/1w_L3S346encBQejQjBFWj2f1-25uVqxtfCQt5bzMd7Q/edit?usp=sharing', icon_type='glyph', icon_value='glyphicon-book'))
admin.add_view(CalendarView(Calendar, db.session, name="My Calendars", endpoint="calendar", menu_icon_type='glyph', menu_icon_value='glyphicon-calendar'))
admin.add_view(LocationView(Location, db.session, name="Approved Venues", endpoint="location", menu_icon_type='glyph', menu_icon_value='glyphicon-home'))
admin.add_view(EventView(Event, db.session, name="Pending Events", endpoint="event", menu_icon_type='glyph', menu_icon_value='glyphicon-time'))
admin.add_view(SettingsView(name="Settings", endpoint="settings", menu_icon_type='glyph', menu_icon_value='glyphicon-wrench'))

admin.add_link(NotAuthenticatedMenuLink(name='Login With Google', endpoint='login', icon_type='glyph', icon_value='glyphicon-log-in'))
admin.add_link(AuthenticatedMenuLink(name='Logout', endpoint='logout', icon_type='glyph', icon_value='glyphicon-log-out'))