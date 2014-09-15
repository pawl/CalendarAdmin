from flask import redirect, flash, session, g, url_for, request
from application import app, db
from application.models import User
from application.helpers import is_valid_credentials
		   
@app.route('/subaccount_logout/<provider_name>/', methods=['GET', 'POST'])
def subaccount_logout(provider_name):
	if g.user and is_valid_credentials():
		if getattr(g.user, provider_name + "_id"): 
			setattr(g.user, provider_name + "_id", None) # delete user ID
			db.session.commit()
			flash("Your " + provider_name + " account was unlinked successfully", "success")
		else:
			flash("Your " + provider_name + " account was already unlinked successfully", "success")
		if session.get(provider_name):
			del session[provider_name]
		return redirect(url_for('settings.index'))
	else:
		return redirect(url_for('login', next=request.url))