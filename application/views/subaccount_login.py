from flask import redirect, flash, session, g, url_for, request, make_response
from application import app, authomatic, db
from authomatic.adapters import WerkzeugAdapter
from authomatic.exceptions import FailureError, ConfigError
from application.helpers import is_safe_url, credentials, is_valid_credentials
from application.models import User
		   
@app.route('/subaccount_login/<provider_name>/', methods=['GET', 'POST'])
def subaccount_login(provider_name):
	# HACK ALERT: using a normal get request will break the login, so the "next" url needs to be saved to the session and redirected back to normal login
	next = request.args.get('next')
	if next:
		if is_safe_url(next):
			session['next'] = next
		return redirect(url_for('subaccount_login', provider_name=provider_name))	

	# user must be logged in via google
	if g.user and is_valid_credentials(): # better than @login_required decorator - ensures user is logged in and google credentials haven't expired
		if is_valid_credentials(name=provider_name): # no need to log in again
			flash("You were already logged into your " + provider_name + " account.", "success")
			return redirect(url_for('calendar.index_view'))
		else:
			response = make_response()
			try:
				result = authomatic.login(WerkzeugAdapter(request, response), provider_name)
			# user denies access when asked for permission
			except FailureError:
				flash("Permission to add events to your " + provider_name + " account was denied.")
				return redirect(url_for('settings.index'))
			except ConfigError:
				flash("Invalid login option.")
				return redirect(url_for('settings.index'))

			if result:
				result.user.update() # user result object won't have any data without this
				session[provider_name] = result.user.credentials.serialize() # add newest token to session (refreshes credentials)
				
				# if no _id exists or it's different - create user
				if not (getattr(g.user, provider_name + "_id") and (getattr(g.user, provider_name + "_id") == result.user.id)): 
					setattr(g.user, provider_name + "_id", result.user.id)
					db.session.commit()
					
					# special logic for grabbing meetup group ID (required for future requests)
					if (provider_name == "meetup"):
						try:
							meetup_response = authomatic.access(credentials(name="meetup"), 'https://api.meetup.com/2/groups?&group_urlname=' + getattr(g.user, "meetup_group_name"), method='GET')
							g.user.meetup_group_id = meetup_response.data['results'][0]['id']
							db.session.commit()
							flash("Your " + provider_name + " account was linked successfully", "success")
						except:
							g.user.meetup_group_id = None
							
						# if it fails to get the ID, unlink meetup account
						if not g.user.meetup_group_id:
							g.user.meetup_group_name = None
							g.user.meetup_group_id = None
							g.user.meetup_id = None
							db.session.commit()
							if session.get("meetup"):
								del session["meetup"]
							flash("Failed to find your meetup group. Please attempt to link your Meetup account again with the correct URL.")
							return redirect(url_for('settings.index'))
			else:
				return response # won't redirect the user to login at meetup/eventbrite without this
				
			return redirect(session.pop('next', False) or url_for('settings.index'))
	else:
		return redirect(url_for('login', next=request.url))