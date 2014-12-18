import urllib
import json
import datetime
import wtforms
import os
import arrow

from application.views.custom_model_view import CustomModelView
from wtforms import form, fields, validators
from wtforms.validators import ValidationError
from application.models import Calendar, Event, Location, User
from application.helpers import decrypt_string, is_valid_credentials, credentials, encrypt_string
from application import app, db, mandrill, authomatic
from flask import request, redirect, flash, url_for, g, get_flashed_messages
from flask.ext.admin import expose
from flask.ext.admin.actions import action
from sqlalchemy.orm.exc import NoResultFound

class EventView(CustomModelView):
    #TODO: override action_delete and send email for deny too
    new_actions = True # used for triggering new_actions macro in list.html
    
    column_list = (
        'summary', 
        'start',
        'end',
        'location',
        'calendar',
        'requester_name',
        'requester_email',
    )
    column_labels = {
        'summary': 'Event Title', 
        'start': 'Start Time', 
        'end': 'End Time', 
        'description': 'Event Description',
    }
    form_columns = (
        'summary', 
        'start', 
        'end', 
        'description', 
        'requester_name', 
        'requester_email', 
        'to_meetup', 
        'to_eventbrite', 
        'location', 
        'calendar',
    )
    
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
        end=dict(
            validators=[end_must_be_greater, end_must_not_conflict],
            format='%Y-%m-%d %H:%M'
        ), # required validator is not necessary, already included
        start=dict(
            validators=[start_must_not_conflict, must_be_future],
            format='%Y-%m-%d %H:%M'
        ),
        requester_email=dict(
            validators=[wtforms.validators.Email(message=u'Invalid email address.')]
        )
    )
    
    # form in request.html is set statically, this mainly applies to edit/create page 
    form_widget_args = dict(
        end={'data-date-format': u'YYYY-MM-DD HH:mm'},
        start={'data-date-format': u'YYYY-MM-DD HH:mm'},
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
            To Meetup: %s
            To Eventbrite: %s
            Location: %s
                    
            Link to Approve: %s
            
            Link to Deny: %s
            
            Link to Modify: %s
            """ % (event.summary, event.start, event.end, event.description, event.requester_name, event.requester_email, event.to_meetup, event.to_eventbrite, event.location.title, approve_url, deny_url, modify_url)
            
            email_addresses = [{'email': user.email} for user in result_calendar.users]
            mandrill.send_email(
                from_email="admin@calendaradmin.com",
                subject="New Calendar Admin Request",
                to=email_addresses,
                text=text.replace('    ','')  # remove wacky indentions
            )
            
            unescaped_url = urllib.unquote(urllib.unquote(redirect_url))
            if ('http://' in unescaped_url) or ('https://' in unescaped_url):
                return redirect(unescaped_url, code=302) # TODO: need to redirect to url given by user in request
            else:
                return redirect("http://"+unescaped_url, code=302) # TODO: need to redirect to url given by user in request
        
        # location information dictionary for form
        locations = [{'id': location.id, 'image': location.image_url, 'description': location.description} for location in result_calendar.locations] 
        
        return self.render('request.html', form=form, locations=locations, eventbrite_disabled=result_calendar.eventbrite_disabled, google_disabled=result_calendar.google_disabled, meetup_disabled=result_calendar.meetup_disabled)
        
    @action('approve', 'Approve')
    def action_approve(self, ids):
        # TODO: make sure user can only approve their own items
        if not ids:
            flash("No events selected.")
            return redirect(url_for('event.index_view'))
            
        for id in ids:
            event_object = Event.query.get(int(id))
            if event_object:
                errors = False
                
                # check if user is logged into google - mandatory
                if not is_valid_credentials():
                    return redirect(url_for('login', next=url_for('event.index_view'))) 
                
                # TODO: combine meetup and eventbrite login checks into one
                # check if login is required for meetup or eventbrite, and redirect to login
                # this must be before the requests or it will cause duplicate event submissions!
                if event_object.to_meetup and not event_object.calendar.meetup_disabled:
                    if g.user.meetup_id:
                        if not is_valid_credentials(name="meetup"):
                            flash('Credentials required refreshing. Try approving your event again.')
                            return redirect(url_for('subaccount_login', provider_name="meetup", next=url_for('event.index_view')))
                    else:
                        # check to see if other users have meetup linked, if yes - direct the user to settings
                        if any([(user.meetup_id and g.user.id != user.id) for user in event_object.calendar.users]):
                            flash('Other owners of this calendar have a Meetup account linked. Please link your Meetup account.')
                        else:
                            flash('Approving this event requires your Meetup account to be linked. Please link your Meetup account.')
                        return redirect(url_for('settings.index'))
                    
                if event_object.to_eventbrite and not event_object.calendar.eventbrite_disabled:
                    if g.user.eventbrite_id:
                        if not is_valid_credentials(name="eventbrite"):
                            flash('Credentials required refreshing. Try approving your event again.')
                            return redirect(url_for('subaccount_login', provider_name="eventbrite", next=url_for('event.index_view')))
                    else:
                        # check to see if other users have eventbrite linked, if yes - direct the user to settings
                        if any([(user.eventbrite_id and g.user.id != user.id) for user in event_object.calendar.users]):
                            flash('Other owners of this calendar have a Eventbrite account linked. Please link your Eventbrite account.')
                        else:
                            flash('Approving this event requires your Eventbrite account to be linked. Please link your Eventbrite account.')
                        return redirect(url_for('settings.index'))
                        
                ###########################
                # GOOGLE CALENDAR
                ###########################
                #if not event_object.calendar.google_disabled and event_object.to_google: # for when Google Calendar can be disabled
                
                # +'Z' is short-hand for GMT timezone
                google_find_duplicate_params = {
                    "timeMin": event_object.start.isoformat()+'Z',
                    "timeMax": event_object.end.isoformat()+'Z',
                    "timeZone": event_object.calendar.timezone
                }
                google_find_duplicates_response = authomatic.access(credentials(), 'https://www.googleapis.com/calendar/v3/calendars/' + urllib.quote(event_object.calendar.calendar_id) + '/events', params=google_find_duplicate_params)
                try:
                    existing_events = [event for event in google_find_duplicates_response.data['items'] if (event_object.location.title == event['location']) or (event_object.summary == event['summary'])]
                except KeyError:
                    app.logger.error(event)
                    raise
                
                if not any(existing_events):
                    google_add_event_requestbody = {
                        "start": {
                            "dateTime": event_object.start.isoformat(),
                            "timeZone": event_object.calendar.timezone
                        },
                        "end": {
                            "dateTime": event_object.end.isoformat(),
                            "timeZone": event_object.calendar.timezone
                        },
                        "description": event_object.description,
                        "location": event_object.location.title,
                        "summary": event_object.summary
                    }
                    url = 'https://www.googleapis.com/calendar/v3/calendars/' + urllib.quote(event_object.calendar.calendar_id) + '/events'
                    google_add_event_response = authomatic.access(credentials(), url, method='POST', headers={'Content-Type': 'application/json'}, body=json.dumps(google_add_event_requestbody))
                    #print "google", google_response
                    if google_add_event_response.status != 200:
                        flash('There was an error approving your google calendar event. Error Code: ' + str(google_add_event_response.status) + ' Reason: ' + google_add_event_response.reason)
                        errors = True
                else:
                    flash('A similar event already exists in your google calendar.')
                
                
                ##############
                # MEETUP
                ##############
                if event_object.to_meetup and not event_object.calendar.meetup_disabled:                    
                    # workaround for address_1_error, see if venue exists first
                    meetup_venue_request_params = {
                        "group_urlname": g.user.meetup_group_name
                    }                   
                    meetup_venue_response = authomatic.access(credentials(name="meetup"), 'https://api.meetup.com/2/venues.json/', meetup_venue_request_params)
                    
                    # try to find a matching venue
                    meetup_venue_id = None
                    for venue in meetup_venue_response.data['results']:
                        if (event_object.location.title == venue['name']): #or (event_object.location.address == venue['address_1']):
                            meetup_venue_id = venue['id']
                    
                    if meetup_venue_id is None:
                        # create venue if it doesn't exist, otherwise use the returned possible match
                        # somehow this is passed to authomatic as a param and it's escaped, no json + json header required
                        meetup_create_venue_requestbody = {
                            "address_1": event_object.location.address,
                            "city": event_object.location.city,
                            "name": event_object.location.title,
                            "state": event_object.location.state,
                            "country": event_object.location.country
                        }
                        meetup_venue_response = authomatic.access(credentials(name="meetup"), 'https://api.meetup.com/' + g.user.meetup_group_name + '/venues', meetup_create_venue_requestbody, method="POST")
                        
                        meetup_venue_id = None
                        if meetup_venue_response.status == 409:
                            meetup_venue_id = meetup_venue_response.data['errors'][0]['potential_matches'][0]['id'] #TODO: make this more accurate and actually get the most similar venue
                        elif meetup_venue_response.status == 201:
                            meetup_venue_id = meetup_venue_response.data['id']
                        elif meetup_venue_response.status == 400:
                            reasons = ", ".join([error['code'] for error in meetup_venue_response.data['errors']])
                            flash('There was an error adding a venue to your meetup. Error Code: ' + str(meetup_venue_response.status) + ' Reason: ' + reasons)
                            if "address_1_error" in reasons:
                                flash("Try adding a zip-code to your venue's address.")
                            errors = True
                        else: # error status without reasons, could be 404
                            flash('There was an error adding a venue to your meetup. Error Code: ' + str(meetup_venue_response.status))
                            errors = True
                    
                    if meetup_venue_id:
                        meetup_start = arrow.get(event_object.start, event_object.calendar.timezone)
                        meetup_start = (meetup_start-meetup_start.dst()).to('utc').timestamp # adjust for dst and return timestamp
                        
                        meetup_end = arrow.get(event_object.end, event_object.calendar.timezone)
                        meetup_end = (meetup_end-meetup_end.dst()).to('utc').timestamp 
                        
                        meetup_requestbody = {
                            "group_id": g.user.meetup_group_id,
                            "group_urlname": g.user.meetup_group_name,
                            "name": event_object.summary.encode('utf-8'), # fix "'ascii' codec can't encode character"
                            "duration": (meetup_end*1000) - (meetup_start*1000),
                            "time": meetup_start*1000,
                            "description": event_object.description.encode('utf-8'),
                            "venue_id": meetup_venue_id,
                            "publish_status": "published"
                        }
                        meetup_response = authomatic.access(credentials(name="meetup"), 'https://api.meetup.com/2/event.json/', meetup_requestbody, method="POST")
                        if meetup_response.status != 201:
                            flash('There was an error approving your meetup event. Error Code: ' + str(meetup_response.status) + ' Reason: ' + meetup_response.reason)
                            errors = True
                
                #######################
                # EVENTBRITE
                #######################
                if event_object.to_eventbrite and not event_object.calendar.eventbrite_disabled:                        
                    # attempt to create organizer
                    eventbrite_organizer_requestbody = {
                        "name": event_object.requester_name,
                        "description": ""
                    }
                    eventbrite_organizer_response = authomatic.access(credentials(name="eventbrite"), 'https://www.eventbrite.com/json/organizer_new', eventbrite_organizer_requestbody, method="POST")
                    
                    if 'error' in eventbrite_organizer_response.data:
                        # search for organizers and pick the first one
                        eventbrite_organizer_response = authomatic.access(credentials(name="eventbrite"), 'https://www.eventbrite.com/json/user_list_organizers')
                        try:
                            organizer_id = None
                            for organizer in eventbrite_organizer_response.data['organizers']:
                                if organizer['organizer']['name'] == event_object.requester_name:
                                    organizer_id = organizer['organizer']['id']
                            if organizer_id == None:
                                organizer_id = eventbrite_organizer_response.data['organizers'][0]['organizer']['id'] # give up, just pick the first one
                        except:
                            flash('There was an error while retrieving organizers from your eventbrite.')
                            return redirect(url_for('event.index_view'))
                    elif 'process' in eventbrite_organizer_response.data:
                        organizer_id = eventbrite_organizer_response.data['process']['id']
                    else:
                        flash('There was an error while adding an organizer to your eventbrite.')
                        return redirect(url_for('event.index_view'))
                    
                    # get a list of venues
                    try:
                        eventbrite_venue_response = authomatic.access(credentials(name="eventbrite"), 'https://www.eventbrite.com/json/user_list_venues')
                    except:
                        flash('There was an error while retrieving venues from your eventbrite.')
                        return redirect(url_for('event.index_view'))
                    
                    # try to find a matching venue
                    eventbrite_venue_id = None
                    for venue in eventbrite_venue_response.data['venues']:
                        if event_object.location.title == venue['venue']['name']:
                            eventbrite_venue_id = venue['venue']['id']
                    
                    # create a venue if one isn't found, possible bug: allows creating infinite duplicates
                    if eventbrite_venue_id is None:
                        # attempt to create venue
                        eventbrite_venue_requestbody = {
                            "organizer_id": organizer_id,
                            "address": event_object.location.address,
                            "city": event_object.location.city,
                            "name": event_object.location.title,
                            "region": event_object.location.state,
                            "country_code": event_object.location.country
                        }
                        eventbrite_venue_response = authomatic.access(credentials(name="eventbrite"), 'https://www.eventbrite.com/json/venue_new', eventbrite_venue_requestbody, method="POST")
                        if 'process' in eventbrite_venue_response.data:
                            eventbrite_venue_id = eventbrite_venue_response.data['process']['id']
                        else:
                            flash('There was an error adding an venue to your eventbrite.')
                            return redirect(url_for('event.index_view'))
                    
                    eventbrite_requestbody = {
                        "organizer_id": organizer_id,
                        "venue_id": eventbrite_venue_id,
                        "start_date": event_object.start.strftime("%Y-%m-%d %H:%M:%S"),
                        "end_date": event_object.end.strftime("%Y-%m-%d %H:%M:%S"),
                        "title": event_object.summary.encode('utf-8'),
                        "timezone": event_object.calendar.timezone,
                        "description": event_object.description.encode('utf-8'),
                        "privacy": 1,
                        "status": "live"
                    }
                    eventbrite_response = authomatic.access(credentials(name="eventbrite"), 'https://www.eventbrite.com/json/event_new', eventbrite_requestbody, method="POST")
                    if eventbrite_response.data.get('error_message'):
                        flash('There was an error approving your eventbrite event. Error Code: ' + str(eventbrite_response.status) + ' Reason: ' + eventbrite_response.reason)
                        errors = True
                    
                if not errors:
                    # email all the other users who could have approved the event
                    text = """The following event has been approved:
                    Event Title: %s
                    Start Time: %s
                    End Time: %s
                    Event Description: %s
                    Requester Name: %s
                    Requester E-mail: %s
                    To Meetup: %s
                    To Eventbrite: %s
                    Location: %s
                    """ % (event_object.summary,
                           event_object.start.strftime("%Y-%m-%d %H:%M"),
                           event_object.end.strftime("%Y-%m-%d %H:%M"), 
                           event_object.description, 
                           event_object.requester_name, 
                           event_object.requester_email, 
                           event_object.to_meetup, 
                           event_object.to_eventbrite, 
                           event_object.location.title)
                    email_addresses = [{'email': user.email} for user in event_object.calendar.users if user.email != g.user.email] + [{'email': event_object.requester_email}]
                    print email_addresses
                    mandrill.send_email(
                        from_email="admin@gcalmanager.com",
                        subject="Calendar Admin Request Approved",
                        to=email_addresses,
                        text=text.replace('    ','') # remove wacky indentions 
                    )
                    
                    # delete item on approval
                    # probably need to save it and add "approved by"
                    Event.query.filter(db.and_(Event.id == event_object.id)).delete(synchronize_session=False)
                    db.session.commit()
                    
                    flash('The selected events were approved.')
                    
                if request.endpoint == "event.approve_view":
                    return '<b>' + ", ".join(get_flashed_messages()) + '</b>'
                else:
                    return redirect(url_for('event.index_view'))
            else:
                return '<b>Event not found. Ensure URL is correct.</b>'
                
    # TODO: ensure approve and deny links are always different, so users can't click links in old emails to deny other's requests
    @expose('/approve/<id>', methods=('GET', 'POST'))
    def approve_view(self, id):
        id = decrypt_string(id)
        return self.action_approve([id])
        
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