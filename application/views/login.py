from flask import redirect, flash, session, g, url_for, request, make_response
from flask.ext.login import logout_user, login_required, login_user
from application import app, authomatic, db
from authomatic.adapters import WerkzeugAdapter
from authomatic.exceptions import FailureError, ConfigError
from sqlalchemy.orm.exc import NoResultFound
from application.helpers import is_safe_url, credentials
from application.models import User
		   
@app.route('/login', methods=['GET', 'POST'])
@app.route('/login/<provider_name>/', methods=['GET', 'POST'])
def login(provider_name="google"): # TODO: add a parameter to allow this to work for meetup login too
	# HACK ALERT: using a normal get request will break the login, so the "next" url needs to be saved to the session and redirected back to normal login
	next = request.args.get('next')
	if next:
		if is_safe_url(next):
			session['next'] = next
		return redirect(url_for('login'))		
		
	if g.user and g.user.is_authenticated() and credentials().valid:
		flash("You are already logged in.")
		return redirect(session.pop('next', False) or '/')
		
	response = make_response()
	
	try:
		result = authomatic.login(WerkzeugAdapter(request, response), provider_name)
	# user denies access when asked for permission
	except FailureError:
		flash("Permission to access your calendar was denied.")
		raise
		return redirect('/')
	except ConfigError:
		flash("Invalid login option.")
		return redirect('/')
			
	if result:
		if result.user:
			result.user.update()
			try:
				user = User.query.filter(User.google_id == str(result.user.id)).one()
			except NoResultFound: # create user if none exists
				user = User(google_id = str(result.user.id), name = result.user.name, email = result.user.email)
				db.session.add(user)
				db.session.commit()
			session['credentials'] = result.user.credentials.serialize()
			login_user(user)
			flash("You were logged in successfully.", "success")
		return redirect(session.pop('next', False) or '/') # clear the session variable to prevent always going to the same page
		
	return response	