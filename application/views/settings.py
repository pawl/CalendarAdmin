from flask.ext.admin import BaseView, expose
from flask import g, redirect, url_for, request
from application.helpers import is_valid_credentials
from application import db

def is_provider_linked(provider):
	if getattr(g.user, provider + "_id"):
		return True
	else:
		return False
		
class SettingsView(BaseView):
	def is_accessible(self):
		return is_valid_credentials()
		
	def _handle_view(self, name, **kwargs):
		if not self.is_accessible():
			return redirect(url_for('login', next=request.url))
			
	@expose('/', methods=('GET', 'POST'))
	def index(self):
		if request.method == 'POST':
			# TODO: add validation
			setattr(g.user, "meetup_url", request.form['meetup_url'])
			db.session.commit()
			return redirect(url_for('subaccount_login', provider_name="meetup"))
		return self.render('settings.html', meetup_enabled=is_provider_linked("meetup"), eventbrite_enabled=is_provider_linked("eventbrite"))