import flask_wtf

from flask.ext.admin.contrib.sqla import ModelView
from application.helpers import is_valid_credentials
from flask import request, redirect, url_for

# used to override original ModelView to keep code in other models DRY
class CustomModelView(ModelView):
	edit_template = 'edit.html' # remove extra button
	create_template = 'create.html' # remove save and continue
	list_template = 'list.html'
	new_actions = False # used for triggering new_actions macro in list.html
	
	# allows preventing CSRF
	form_base_class = flask_wtf.Form
	
	# can't return redirect in is_accessible or it will cause errors
	def _handle_view(self, name, **kwargs):
		if not self.is_accessible():
			return redirect(url_for('login', next=request.url))
			
	def is_accessible(self):
		return is_valid_credentials()