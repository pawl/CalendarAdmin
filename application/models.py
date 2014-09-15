from application import db

class User(db.Model):
	__tablename__ = 'user'
	id = db.Column(db.Integer, primary_key=True)
	google_id = db.Column(db.String(255)) # should be unique?
	meetup_id = db.Column(db.String(255))
	meetup_url = db.Column(db.String(255))
	eventbrite_id = db.Column(db.String(255))
	name = db.Column(db.String(255))
	email = db.Column(db.String(255))
		
	def is_authenticated(self):
		return True

	def is_anonymous(self):
		return False
		
	def is_active(self):
		return True
		
	def get_id(self):
		return unicode(self.id)
		
	def __repr__(self):
		return self.name
		
# for many-to-many relation, many users have the calendar (and vice versa)
users_and_calendars = db.Table('users_and_calendars',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('calendar_id', db.Integer, db.ForeignKey('calendar.id'))
)

class Calendar(db.Model):
	__tablename__ = 'calendar'
	id = db.Column(db.Integer, primary_key=True)
	calendar_id = db.Column(db.String(255)) # string - Identifier of the calendar.
	summary = db.Column(db.String(255)) # string - Title of the calendar. Read-only.
	timezone = db.Column(db.String(255)) # string - The time zone of the calendar. Optional. Read-only.
	url = db.Column(db.String(255))
	enabled = db.Column(db.Boolean())
	redirect_url = db.Column(db.Text())
	google_disabled = db.Column(db.Boolean())
	meetup_disabled = db.Column(db.Boolean())
	eventbrite_disabled = db.Column(db.Boolean())
	
	users = db.relationship('User', secondary=users_and_calendars, backref=db.backref('calendars', lazy='dynamic')) # many-to-many relationship
	events = db.relationship("Event", backref=db.backref('calendar'))
	locations = db.relationship("Location", backref=db.backref('calendar')) # TODO: make this MANY-TO-MANY

	def __repr__(self):
		return self.summary
		
	def __init__(self, calendar_id, summary, timezone):
		self.calendar_id = calendar_id
		self.summary = summary
		self.timezone = timezone

class Event(db.Model):
	__tablename__ = 'event'
	id = db.Column(db.Integer, primary_key=True)
	#event_id = db.Column(db.String(255)) # string - Identifier of the event. Not needed since we're not tracking this.
	summary = db.Column(db.String(255), nullable=False) # string - Title of the event.
	start = db.Column(db.DateTime(), nullable=False) 
	end = db.Column(db.DateTime(), nullable=False)
	description = db.Column(db.Text(), nullable=False)
	
	requester_name = db.Column(db.String(255), nullable=False)
	requester_email = db.Column(db.String(255), nullable=False)
	
	to_google = db.Column(db.Boolean())
	to_eventbrite = db.Column(db.Boolean())
	to_meetup = db.Column(db.Boolean())
	
	#ideas - keep events in the database so you can note who approved it and send reminders
	#archived = db.Column(db.Boolean)
	#reminders = db.Column(db.String(255))
	#approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))	

	location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)					
	calendar_id = db.Column(db.Integer, db.ForeignKey('calendar.id'), nullable=False)
	
	def __repr__(self):
		return self.summary

class Location(db.Model):
	__tablename__ = 'location'
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(255))
	image_url = db.Column(db.String(255))
	description = db.Column(db.Text())
	
	calendar_id = db.Column(db.Integer, db.ForeignKey('calendar.id')) # TODO: make this MANY-TO-MANY to make calendars selectable from Location view
	events = db.relationship("Event", backref='location')
	
	def __repr__(self):
		return self.title
