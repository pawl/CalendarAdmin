import re

from flask.ext.admin import BaseView, expose
from flask import g, redirect, url_for, request, flash
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
		# thought process: asking the user to input the URL of the meetup is more user friendly than explaining the group name
		if request.method == 'POST':
			if ("www.meetup.com" in request.form['meetup_url']) and (6 > len(request.form['meetup_url'].split('/')) > 1):
				if request.form['meetup_url'].split('/')[-2] == "www.meetup.com":
					group_name = request.form['meetup_url'].split('/')[-1]
				else:
					group_name = request.form['meetup_url'].split('/')[-2]
			else:
				flash('Invalid Meetup URL. Your URL look like this: http://www.meetup.com/dallasmakerspace/')
				return redirect(url_for('settings.index'))
				
			if re.match('^[\w-]+$', group_name) is not None: # is valid group name
				setattr(g.user, "meetup_url", request.form['meetup_url'])
				setattr(g.user, "meetup_group_name", group_name)
				db.session.commit()
				return redirect(url_for('subaccount_login', provider_name="meetup"))
			else:
				flash('Invalid Meetup URL. Your URL look like this: http://www.meetup.com/dallasmakerspace/')
				return redirect(url_for('settings.index'))
			
		return self.render('settings.html', meetup_enabled=is_provider_linked("meetup"), eventbrite_enabled=is_provider_linked("eventbrite"))