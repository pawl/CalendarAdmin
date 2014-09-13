from authomatic.providers.oauth2 import OAuth2

# credit to: https://github.com/morgante/nyuadcoursereview/blob/master/app/oauthLogin.py
class EventbriteProvider(OAuth2):
	# URL where the user will be redirected and asked to grant permissions to your app.
	user_authorization_url = 'https://www.eventbrite.com/oauth/authorize'
	# URL where your app will exchange the request_token for access_token.
	access_token_url = 'https://www.eventbrite.com/oauth/token'
	# API endpoint where you can get the user's profile info.
	user_info_url = 'https://www.eventbriteapi.com/v3/users/me'

	# Optional minimum scope needed to get the user's profile info.
	user_info_scope = []
	
	#The AuthorizationProvider.type_id is a unique numeric ID
	#assigned to each provider used by serialization and deserialization of credentials. It is automatically generated from the PROVIDER_ID_MAP
	#Just override the type_id getter with a static property in your subclass with any integer greater than 16
	type_id = 100017
	
	@staticmethod
	def _x_user_parser(user, data):
		"""
		Use this to populate the User object with data from JSON
		returned by provider on User.update().
		
		http://developer.eventbrite.com/doc/users/
		"""	  
		
		user.user_id = data.get('user_id')
		user.email = data.get('email')
		user.first_name = data.get('first_name')
		user.last_name = data.get('last_name')
		user.user_key = data.get('user_key')
		user.date_created = data.get('date_created')
		user.date_modified = data.get('date_modified')
		user.subusers = data.get('subusers')
		
		return user