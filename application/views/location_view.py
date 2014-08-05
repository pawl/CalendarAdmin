from application.views.custom_model_view import CustomModelView
from application.models import Location, Calendar, User
from flask import g

class LocationView(CustomModelView):
	# Override displayed fields
	column_list = ('title','calendar')
	column_labels = {'title': 'Possible Event Location (free-form text)', 'calendar': 'Applicable Calendars'}
	form_excluded_columns = ('events',)
	
	def get_query(self):
		return Location.query.join(Location.calendar).filter(Calendar.users.any(User.id == g.user.id))
			
	# override forms to prevent users from seeing eachother's data: https://gist.github.com/mrjoes/5521548
	# Hook form creation methods
	def create_form(self):
		return self._use_filtered_parent(super(LocationView, self).create_form())
 
	def edit_form(self, obj):
		return self._use_filtered_parent(super(LocationView, self).edit_form(obj))
 
	def _use_filtered_parent(self, form):
		form.calendar.query_factory = self._get_parent_list
		return form
 
	def _get_parent_list(self):
		return Calendar.query.filter(Calendar.users.any(User.id == g.user.id)).all()