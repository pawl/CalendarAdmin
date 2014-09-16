import urllib
import json
import datetime
import wtforms
import os

from application.views.custom_model_view import CustomModelView
from wtforms import form, fields, validators
from wtforms.validators import ValidationError
from application.models import Calendar, Event, Location, User
from application.helpers import decrypt_string, is_valid_credentials, credentials, encrypt_string
from application import app, db, mandrill, authomatic
from flask import request, redirect, flash, url_for, g
from flask.ext.admin import expose
from flask.ext.admin.actions import action
from sqlalchemy.orm.exc import NoResultFound

class EventView(CustomModelView):
	#TODO: override action_delete and send email for deny too
	new_actions = True # used for triggering new_actions macro in list.html
	
	column_list = ('summary', 'start', 'end', 'location', 'calendar', 'requester_name', 'requester_email')
	column_labels = {'summary': 'Event Title', 'start': 'Start Time', 'end': 'End Time', 'description': 'Event Description'}
		
	def must_be_future(form, field):
		if form.start.data and (form.start.data < datetime.datetime.now()):
			raise ValidationError('Start time must be greater than current time.')
	# add end date must be greater than start date validation
	def end_must_be_greater(form, field):
		if form.end.data and form.start.data and (form.end.data < form.start.data):
			raise ValidationError('End date must be greater than the start date.')
	#TODO: combine start_must_not_conflict and end_must_not_conflict?
	def start_must_not_conflict(form, field):
		# exclude currently edited id
		if Event.query.filter(db.and_(Event.location == form.location.data, Event.start.between(form.start.data, form.end.data), Event.id != request.args.get('id'))).first():
			raise ValidationError('Start time conflicts with another request for the same time.')
	def end_must_not_conflict(form, field):
		if Event.query.filter(db.and_(Event.location == form.location.data, Event.end.between(form.start.data, form.end.data), Event.id != request.args.get('id'))).first():
			raise ValidationError('End time conflicts with another request for the same time.')
			
	form_args = dict(
		end=dict(validators=[end_must_be_greater, end_must_not_conflict], format='%m/%d/%Y %I:%M %p'), # required validator is not necessary, already included
		start=dict(validators=[start_must_not_conflict, must_be_future], format='%m/%d/%Y %I:%M %p'),
		requester_email=dict(validators=[wtforms.validators.Email(message=u'Invalid email address.')])
	)
	
	@expose('/request/<calendar_id>/<redirect_url>', methods=('GET', 'POST'))
	def request_view(self, calendar_id, redirect_url):
		# ensure calendar id is enabled
		try:
			result_calendar = Calendar.query.filter(db.and_(Calendar.id == unicode(decrypt_string(calendar_id)), Calendar.enabled == True)).one()
		except NoResultFound:
			flash('Calendar disabled or calendar does not exist. Ensure URL was entered correctly.')
			return redirect('/')
		
		self.calendar_id = decrypt_string(calendar_id) # used in _get_parent_list_location
		form = self.create_form()
		form.__delitem__('calendar') # remove calendar as a selection option from the form - the URL selects the calendar
		if request.method == 'POST' and form.validate():
			event = Event()
			form.populate_obj(event)
			event.calendar = result_calendar
			db.session.add(event)
			db.session.commit()

			users = Calendar.query.filter(Calendar.id == self.calendar_id).one().users
			approve_url = app.config['DOMAIN_NAME'] + '/event/approve/' + encrypt_string(event.id)
			deny_url = app.config['DOMAIN_NAME'] + '/event/deny/' + encrypt_string(event.id)
			modify_url = app.config['DOMAIN_NAME'] + '/event/modify/' + encrypt_string(event.id)
			text = """The following event has been submitted for your approval:
			Event Title: %s
			Start Time: %s
			End Time: %s
			Event Description: %s
			Requester Name: %s
			Requester E-mail: %s
			Location: %s
					
			Link to Approve: %s
			
			Link to Deny: %s
			
			Link to Modify: %s
			""" % (event.summary, event.start, event.end, event.description, event.requester_name, event.requester_email, event.location.title, approve_url, deny_url, modify_url)
			
			email_addresses = [{'email': user.email} for user in users]
			mandrill.send_email(
				from_email="admin@calendaradmin.com",
				subject="New Calendar Admin Request",
				to=email_addresses,
				text=text.replace('\t','')  # remove wacky indentions
			)
			
			unescaped_url = urllib.unquote(urllib.unquote(redirect_url))
			if ('http://' in unescaped_url) or ('https://' in unescaped_url):
				return redirect(unescaped_url, code=302) # TODO: need to redirect to url given by user in request
			else:
				return redirect("http://"+unescaped_url, code=302) # TODO: need to redirect to url given by user in request
		
		# location information dictionary for form
		locations = [{'id': location.id, 'image': location.image_url, 'description': location.description} for location in result_calendar.locations] 
		
		return self.render('request.html', form=form, locations=locations)
		
	@action('approve', 'Approve')
	def action_approve(self, ids):
		try:
			# TODO make sure user can only approve their own items
			for event_object in Event.query.filter(db.and_(Event.id.in_(ids))).all():
				start = event_object.start.isoformat() #proper rfc 3339 time format for google calendar api
				end = event_object.end.isoformat()
				timezone = event_object.calendar.timezone # without the timezone, you have specify an offset as part of the dateTime
				google_requestbody = """{
				 "start": {
				  "dateTime": "%s",
				  "timeZone": "%s"
				 },
				 "end": {
				  "dateTime": "%s",
				  "timeZone": "%s"
				 },
				 "description": %s,
				 "location": %s,
				 "summary": %s
				}
				""" % (start, timezone, end, timezone, json.dumps(event_object.description), json.dumps(event_object.location.title), json.dumps(event_object.summary))
				url = 'https://www.googleapis.com/calendar/v3/calendars/' + urllib.quote(event_object.calendar.calendar_id) + '/events'
				google_response = authomatic.access(credentials(), url, method='POST', headers={'Content-Type': 'application/json'}, body=google_requestbody)
				#print "google", google_response
				if google_response.status != 200:
					flash('There was an error approving your google calendar event. Error Code: ' + str(google_response.status) + ' Reason: ' + google_response.reason)
					errors = True
					
				meetup_requestbody = {
					"group_id": g.user.meetup_group_id,
					"group_urlname": g.user.meetup_group_name,
					"name": event_object.summary,
					"duration": (int(event_object.end.strftime("%s")) * 1000) - (int(event_object.start.strftime("%s")) * 1000),
					"time": (int(event_object.start.strftime("%s")) * 1000),
					"description": event_object.description
				}
				meetup_response = authomatic.access(credentials(name="meetup"), 'https://api.meetup.com/2/event/', meetup_requestbody, method="POST")
				#print "meetup", meetup_response.data
				if meetup_response.status != 201:
					flash('There was an error approving your meetup event. Error Code: ' + str(meetup_response.status) + ' Reason: ' + meetup_response.reason)
					errors = True
					
				eventbrite_requestbody = {
					"start_date": event_object.start.strftime("%Y-%m-%d %H:%M:%S"),
					"end_date": event_object.end.strftime("%Y-%m-%d %H:%M:%S"),
					"title": event_object.summary,
					"timezone": timezone,
					"description": event_object.description
				}
				eventbrite_response = authomatic.access(credentials(name="eventbrite"), 'https://www.eventbrite.com/json/event_new', eventbrite_requestbody, method="POST")
				#print eventbrite_response.data
				if eventbrite_response.data.get('error_message'):
					flash('There was an error approving your eventbrite event. Error Code: ' + str(eventbrite_response.status) + ' Reason: ' + eventbrite_response.reason)
					errors = True
					
				if not errors:
					# delete item on approval
					# probably need to save it and add "approved by"
					Event.query.filter(db.and_(Event.id == event_object.id)).delete(synchronize_session=False)
					
					# email all the other users who could have approved the event
					text = """The following event has been approved:
					Event Title: %s
					Start Time: %s
					End Time: %s
					Event Description: %s
					Requester Name: %s
					Requester E-mail: %s
					Location: %s
					""" % (event_object.summary, event_object.start.strftime("%Y-%m-%d %H:%M"), event_object.end.strftime("%Y-%m-%d %H:%M"), event_object.description, event_object.requester_name, event_object.requester_email, event_object.location.title)
					email_addresses = [{'email': user.email} for user in event_object.calendar.users if user.email != g.user.email]
					mandrill.send_email(
						from_email="admin@gcalmanager.com",
						subject="Calendar Admin Request Approved",
						to=email_addresses,
						text=text.replace('\t','') # remove wacky indentions 
					)
					flash('The selected events were approved.')
					
			db.session.commit()
		except Exception as ex:
			raise
			#flash(gettext('Failed to add events to your Google Calendar. %(error)s', error=str(ex)), 'error')
			
	# TODO: ensure approve and deny links are always different, so users can't click links in old emails to deny other's requests
	@expose('/approve/<id>', methods=('GET', 'POST'))
	def approve_view(self, id):
		# TODO: consolidate this into a function if possible
		if not is_valid_credentials():
			return redirect(url_for('login', next=request.url))
		# TODO: give accurate indication of success
		id = decrypt_string(id)
		if Event.query.get(int(id)):
			self.action_approve([id])
			return '<b>Event successfully approved.</b>'
		else:
			return '<b>Event not found or may have already been approved. Ensure URL is correct.</b>'
		
	@expose('/deny/<id>', methods=('GET', 'POST'))
	def deny_view(self, id):
		if not is_valid_credentials():
			return redirect(url_for('login', next=request.url))
		id = decrypt_string(id)
		if Event.query.get(int(id)):
			self.action_delete([id])
			return '<b>Event successfully denied.</b>'
		else:
			return '<b>Event not found or may have already been denied. Ensure URL is correct.</b>'
	
	@expose('/modify/<id>', methods=('GET', 'POST'))
	def modify_view(self, id):
		if not is_valid_credentials():
			return redirect(url_for('login', next=request.url))
		id = decrypt_string(id)
		if Event.query.get(int(id)):
			return redirect(url_for('event.edit_view', id=id))
		else:
			return '<b>Event not found. Ensure URL is correct.</b>'
	
	def get_query(self):
		if not Location.query.join(Location.calendar).filter(Calendar.users.any(User.id == g.user.id)).first():
			flash('You need to add an approved venue before you can add an event.')
		if not Calendar.query.filter(Calendar.enabled == True).first():
			flash('You need to enable a calendar before you can add an event.')
		
		return Event.query.join(Event.calendar).filter(Calendar.users.any(User.id == g.user.id))
			
	# TODO: prevent users from accessing records which aren't their own
	def is_accessible(self):
		# bypass for public URL
		if request.endpoint in ['event.request_view']:
			return True
		return is_valid_credentials()
			
	# override forms to prevent users from seeing eachother's data: https://gist.github.com/mrjoes/5521548
	# Hook form creation methods
	def create_form(self):
		return self._use_filtered_parent(super(EventView, self).create_form())
 
	def edit_form(self, obj):
		return self._use_filtered_parent(super(EventView, self).edit_form(obj))
	
	# filter select menus based on the functions below
	def _use_filtered_parent(self, form):
		form.location.query_factory = self._get_parent_list_location
		form.calendar.query_factory = self._get_parent_list_calendar
		return form
 
	# only locations corresponding to the calendar
	def _get_parent_list_location(self):
		if getattr(self, 'calendar_id', None):
			return Location.query.filter(Location.calendar_id == self.calendar_id).all()
		else: # use logged in user's userid
			return Location.query.join(Location.calendar).filter(Calendar.users.any(User.id == g.user.id)).all()
		
	# ensure calendar object is both enabled for management and user.id matches
	def _get_parent_list_calendar(self):
		return Calendar.query.filter(db.and_(Calendar.users.any(User.id == g.user.id), Calendar.enabled == True)).all()