from application.helpers import is_invalid_credentials, is_valid_credentials
from flask.ext.admin.base import MenuLink

# Create menu links classes with reloaded accessible
class AuthenticatedMenuLink(MenuLink):
	def is_accessible(self):
		return is_valid_credentials()

class NotAuthenticatedMenuLink(MenuLink):
	def is_accessible(self):
		return is_invalid_credentials()