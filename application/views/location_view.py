import tempfile
from application.views.custom_model_view import CustomModelView
from application.models import Location, Calendar, User
from flask.ext.admin.form.upload import ImageUploadField, ImageUploadInput
from flask import g, url_for
from application import app
import requests
from base64 import b64encode
import StringIO

# fixes '/static/' before thumbnail URL
class ModifiedImageUploadInput(ImageUploadInput):
	def get_url(self, field):
		if field.thumbnail_size:
			filename = field.thumbnail_fn(field.data)
		else:
			filename = field.data

		if field.url_relative_path:
			filename = filename

		return 'http://i.imgur.com/' + filename + 't.jpg' # small thumbnail
		
# override ImageUploadField to upload images to imgur instead
# idea from quokka: https://github.com/pythonhub/quokka/blob/f89653bbe753319ca204d8e3aba482492f4858fe/quokka/core/admin/fields.py
class ImgurImageField(ImageUploadField):
	widget = ModifiedImageUploadInput()
	
	def _delete_file(self, filename):
		pass
		
	def _save_file(self, data, filename):
		headers = {"Authorization": "Client-ID " + app.config.get("IMGUR_ID")}
		url = "https://api.imgur.com/3/upload.json"

		output = StringIO.StringIO()
		# required this to get it working on ubuntu: http://askubuntu.com/a/272095
		self.image.save(output, self.image.format)
		contents = output.getvalue()
		output.close()
		
		request = requests.post(
			url, 
			headers = headers,
			data = {
				'image': b64encode(contents),
			}
		)
		print request.content
		return request.json()['data']['id']
			
class LocationView(CustomModelView):
	# Override displayed fields
	column_list = ('title','calendar')
	column_labels = {'title': 'Possible Event Location (free-form text)', 'calendar': 'Applicable Calendars', 'image_url': 'Image'}
	form_excluded_columns = ('events',)
	form_overrides = dict(image_url=ImgurImageField)
	
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