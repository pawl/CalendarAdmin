from flask import redirect, flash, session, g, url_for, request, make_response
from flask.ext.login import login_user
from application import app, authomatic, db
from authomatic.adapters import WerkzeugAdapter
from authomatic.exceptions import FailureError, ConfigError
from sqlalchemy.orm.exc import NoResultFound
from application.helpers import is_safe_url, credentials, is_valid_credentials
from application.models import User
		   
# primary login is only with google. meetup and eventbrite accounts are linked
# there's no reliable way to figure out which accounts match up with which accounts if you allow initial login with all 3
@app.route('/login', methods=['GET', 'POST'])
def login():
	# HACK ALERT: using a normal get request will break the login, so the "next" url needs to be saved to the session and redirected back to normal login
	next = request.args.get('next')
	if next:
		if is_safe_url(next):
			session['next'] = next
		return redirect(url_for('login'))		
		
	if g.user and is_valid_credentials():
		flash("You are already logged in.")
		return redirect(session.pop('next', False) or '/')
		
	response = make_response()
	
	try:
		result = authomatic.login(WerkzeugAdapter(request, response), "google")
	except FailureError as e: # happens when user denies access when asked for permission
		flash("Permission to access your calendar was denied.")
		app.logger.error(str(e))
		return redirect('/')
	
	if result:	
		result.user.update() # update the user to get more info
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
	else:	
		return response	# redirect user to login at google's site
