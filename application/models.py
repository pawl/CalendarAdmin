from application import db

class User(db.Model):
	__tablename__ = 'user'
	id = db.Column(db.Integer, primary_key=True)
	google_id = db.Column(db.String(256))
	name = db.Column(db.String(256))
	email = db.Column(db.String(256))
		
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
		
<<<<<<< HEAD
=======
# for many-to-many relation, many users have the calendar (and vice versa)
>>>>>>> a8d7996e7fc7fc06d214069aaf77b02e972baccb
users_and_calendars = db.Table('users_and_calendars',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('calendar_id', db.Integer, db.ForeignKey('calendar.id'))
)

class Calendar(db.Model):
	__tablename__ = 'calendar'
	id = db.Column(db.Integer, primary_key=True)
	calendar_id = db.Column(db.String(256)) # string - Identifier of the calendar.
	summary = db.Column(db.String(256)) # string - Title of the calendar. Read-only.
	timezone = db.Column(db.String(256)) # string - The time zone of the calendar. Optional. Read-only.
	url = db.Column(db.String(256))
	enabled = db.Column(db.Boolean())
	redirect_url = db.Column(db.Text())
	
	users = db.relationship('User', secondary=users_and_calendars, backref=db.backref('calendars', lazy='dynamic')) # many-to-many relationship
		
	events = db.relationship("Event", backref=db.backref('calendar'))
	locations = db.relationship("Location", backref=db.backref("calendar"))
	
	def __repr__(self):
		return self.summary
		
	def __init__(self, calendar_id, summary, timezone):
		self.calendar_id = calendar_id
		self.summary = summary
		self.timezone = timezone
		
class Event(db.Model):
	__tablename__ = 'event'
	id = db.Column(db.Integer, primary_key=True)
	#event_id = db.Column(db.String(256)) # string - Identifier of the event. Not needed since we're not tracking this.
	summary = db.Column(db.String(256), nullable=False) # string - Title of the event.
	start = db.Column(db.DateTime(), nullable=False) 
	end = db.Column(db.DateTime(), nullable=False)
	description = db.Column(db.Text(), nullable=False)
	#reminders = db.Column(db.String(256))
	
	requester_name = db.Column(db.String(256), nullable=False)
	requester_email = db.Column(db.String(256), nullable=False)
	
	#approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))	
	#archived

	location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)					
	calendar_id = db.Column(db.Integer, db.ForeignKey('calendar.id'), nullable=False)
	
	def __repr__(self):
		return self.summary

class Location(db.Model):
	__tablename__ = 'location'
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(256))
	
	calendar_id = db.Column(db.Integer, db.ForeignKey('calendar.id')) 
	events = db.relationship("Event", backref='location')
	
	def __repr__(self):
<<<<<<< HEAD
		return self.title
=======
		return self.title
>>>>>>> a8d7996e7fc7fc06d214069aaf77b02e972baccb
