from authomatic.providers.oauth2 import OAuth2
import authomatic.core as core


class Eventbrite(OAuth2):
    """
    Eventbrite |oauth2| provider.

    * Dashboard: http://www.eventbrite.com/myaccount/apps/
    * Docs: http://developer.eventbrite.com/docs/
    """

    user_authorization_url = 'https://www.eventbrite.com/oauth/authorize'
    access_token_url = 'https://www.eventbrite.com/oauth/token'
    user_info_url = 'https://www.eventbriteapi.com/v3/users/me'

    supported_user_attributes = core.SupportedUserAttributes(
        id=True,
        email=True,
        name=True,
        first_name=True,
        last_name=True,
    )

    type_id = 100017 # prevents AttributeError: 'module' object has no attribute 'PROVIDER_ID_MAP'

    @classmethod
    def _x_credentials_parser(cls, credentials, data):
        credentials.token = data.get('access_token')
        if data.get('token_type') == 'bearer':
            credentials.token_type = cls.BEARER # prevents ValueError: u'bearer' is not in list
        return credentials

    @staticmethod
    def _x_user_parser(user, data):
        """
        Use this to populate the User object with data from JSON
        returned by provider on User.update().
        """

        user.id = data.get('id')
        _emails = data.get('emails', [])
        for email in _emails:
            if email.get('type', '') == 'primary':
                user.email = email.get('address')
                break
        user.first_name = data.get('first_name')
        user.last_name = data.get('last_name')
        user.name = data.get('name')

        return user
