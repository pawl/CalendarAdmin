from flask import redirect, flash, session
from flask.ext.login import logout_user, login_required
from application import app


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Successfully Logged Out')
    return redirect('/')
