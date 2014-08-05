from flask.ext.admin import AdminIndexView
from application.helpers import is_valid_credentials
from flask import redirect, url_for

class MyAdminIndexView(AdminIndexView):
	def is_visible(self):
		return False
		
	def _handle_view(self, name, **kwargs):
		if is_valid_credentials():
			return redirect(url_for('calendar.index_view'))