from flask import redirect, flash, session, g, url_for, request, make_response
from flask.ext.login import login_required
from application import app, authomatic, db
from authomatic.adapters import WerkzeugAdapter
from authomatic.exceptions import FailureError, ConfigError
from sqlalchemy.orm.exc import NoResultFound
from application.helpers import is_safe_url, credentials, is_valid_credentials
from application.models import User
		   
@app.route('/subaccount_login/<provider_name>/', methods=['GET', 'POST'])
def subaccount_login(provider_name):
	# user must be logged in via google
	if g.user and is_valid_credentials(): # better than @login_required decorator - ensures user is logged in and google credentials haven't expired
		if is_valid_credentials(name=provider_name): # no need to log in again
			flash("You were already logged into you " + provider_name + " account.", "success")
			return redirect(url_for('calendar.index_view'))
		else:
			response = make_response()
			try:
				result = authomatic.login(WerkzeugAdapter(request, response), provider_name)
			# user denies access when asked for permission
			except FailureError:
				flash("Permission to add events to your " + provider_name + " account was denied.")
				return redirect('/')
			except ConfigError:
				flash("Invalid login option.")
				return redirect('/')		
								
			try:
				
				if not (getattr(g.user, provider_name + "_id") and (getattr(g.user, provider_name + "_id") == result.user.id)): # create user if none exists, or if the id is different
					result.user.update() # user result object won't have any data without this
					setattr(g.user, provider_name + "_id", result.user.id)
					db.session.commit()
					flash("Your " + provider_name + " account was linked successfully", "success")
				session[provider_name] = result.user.credentials.serialize()
				next = request.args.get('next')
				if next and is_safe_url(next):
					return redirect(next)
				else:
					return redirect(url_for('calendar.index_view')) # subaccount login successful
			except AttributeError:
				return response	
	else:
		return redirect(url_for('login', next=request.url))