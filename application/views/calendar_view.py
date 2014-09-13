import urllib

from application.views.custom_model_view import CustomModelView
from application.models import Calendar, Location, User, MeetupGroup
from application.helpers import encrypt_string, credentials, is_valid_credentials
from application import app, db, authomatic
from flask import flash, g
from flask.ext.admin.actions import action

class CalendarView(CustomModelView):
	#TODO: the pagination needs to be per-user, not for the whole database
	#TODO: add validation to prevent a venue from being added to a calendar which isn't "applicable"
	
	# Override displayed fields
	can_create = False
	can_delete = False
	can_edit = True
	new_actions = True
	column_list = ('summary','enabled','url')
	column_labels = {'summary': 'Calendar Title', 'enabled': 'Calendar Admin Enabled', 'url': 'Public URL for Event Requests', 'locations': 'Approved Event Venues'}
	form_columns = ('locations', 'redirect_url')
	inline_models = [MeetupGroup]
	
	# TODO: clean this up
	column_formatters = dict(url=lambda v, c, m, p: app.config['DOMAIN_NAME']+'/event/request/'+m.url+'/'+urllib.quote_plus(urllib.quote_plus(m.redirect_url)) if (m.redirect_url and m.url) else app.config['DOMAIN_NAME']+'/event/request/'+m.url+'/'+urllib.quote_plus(urllib.quote_plus(app.config['DOMAIN_NAME'])) if (m.url and not m.redirect_url) else "") # show domain name + url if url exists

	@action('disable', 'Disable Selected')
	def action_disable(self, ids):
		try:
			#TODO: You were not the user who originally enabled this calendar. You will need to talk to: 
			Calendar.query.filter(db.and_(Calendar.id.in_(ids), Calendar.users.any(User.id == g.user.id))).update({"enabled": False, "url": None}, synchronize_session=False)
			db.session.commit()
			flash('Calendar Admin was disabled for the selected calendars.')
		except Exception as ex:
			raise
		
	@action('enable', 'Enable Selected')
	def action_enable(self, ids):
		try:
			for id in ids:
				# encrypt url so users can't guess other user's URLs
				calendar_url = encrypt_string(id)
				Calendar.query.filter(db.and_(Calendar.id == id, Calendar.users.any(User.id == g.user.id))).update({"enabled": True, "url": calendar_url}, synchronize_session=False)
				db.session.commit()
			
			flash('Calendar Admin was activated for the selected calendars.')
		except Exception as ex:
			raise
			
	# http://stackoverflow.com/questions/21087077/pre-filter-readable-data-based-on-user-permissions-with-flask-admin
	def get_query(self):
		if not Calendar.query.filter(db.and_(Calendar.users.any(User.id == g.user.id), Calendar.enabled == True)).first():
			flash('You need to enable Calendar Admin on a calendar before your users can submit events for approval.')
		# Grab the user's calendars from Google
		response = authomatic.access(credentials(), 'https://www.googleapis.com/calendar/v3/users/me/calendarList?minAccessRole=writer')
		dictOfCalendars = {}
		#TODO: if calendar's name changes, update it
		for calendar in response.data.get('items'): # get calendars from google
			# if calendar does not exist, then add it
			if Calendar.query.filter(db.and_(Calendar.calendar_id == calendar['id'], ~Calendar.users.any(User.id == g.user.id))).first():
				existing_calendar = Calendar.query.filter(Calendar.calendar_id == calendar['id']).one()
				existing_calendar.users.append(g.user)
				db.session.commit()
			elif not Calendar.query.filter(db.and_(Calendar.calendar_id == calendar['id'], Calendar.users.any(User.id == g.user.id))).first():
				new_calendar = Calendar(calendar['id'], calendar['summary'])
				new_calendar.users.append(g.user)
				db.session.add(new_calendar)
			
		db.session.commit()
		return Calendar.query.filter(Calendar.users.any(User.id == g.user.id))
	
	# override forms to prevent users from seeing eachother's data: https://gist.github.com/mrjoes/5521548
	# Hook form creation methods
	def create_form(self):
		return self._use_filtered_parent(super(CalendarView, self).create_form())
		
	def edit_form(self, obj):
		return self._use_filtered_parent(super(CalendarView, self).edit_form(obj))
		
	# Logic
	def _use_filtered_parent(self, form):
		form.locations.query_factory = self._get_parent_list
		return form
		
	def _get_parent_list(self):
		return Location.query.join(Location.calendar).filter(Calendar.users.any(User.id == g.user.id)).all()