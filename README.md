Calendar Admin
---

Calendar Admin adds the ability to send requests to the administrators of your Google Calendar to have events added. 
It allows you to add an "Add Event" button above your calendar so your users can request events.

### Project Facts
* Uses Python's Flask Web Framework with the Flask-Admin extension.
* Project is designed to be deployed on Heroku, but can be run locally (preferrably an Ubuntu/Debian server) by using "fab run".
* Uses SQLAlchemy (Flask-SQLAlchemy) as the ORM. Locally it uses SQLite, on Heroku it uses Postgres.
* OAUTH authentication made easier by Authomatic.
* Used https://github.com/albertogg/flask-bootstrap-skel for initial boilerplate.
* Admin interface is using the SB Admin 2 theme: http://startbootstrap.com/template-overviews/sb-admin-2/
* Email is handled using Mandrill.
* Alembic is used for database migrations.

### Setup For Development
1. Run "pip install -r requirements/dev.txt" to install requirements.
2. Initialize the DB: https://github.com/albertogg/flask-bootstrap-skel#initialize-db
4. You need to fill in some environmental variables to your etc/environment file:
 * DOMAIN_NAME - Get a domain. This is required for Google login.
 * AUTH (google section)
   * In the Google API Console (APIs section under APIS & AUTH), turn on Calendar API and Google+ API.
    * In the Credentials section of the Google API Console, click "Create new Client ID".
     * Application type: Web Application
      * Use http://www.your_domain.com:8080/login for the AUTHORIZED REDIRECT URI, leave the AUTHORIZED JAVASCRIPT ORIGINS as example.com.
      * GOOGLE_CUSTOMER_KEY  - Use "CLIENT ID"
      * GOOGLE_CUSTOMER_SECRET - Use "CLIENT SECRET"
 * MANDRILL_API_KEY - Get an API key from Mandrill and follow their instructions to set the appropriate DNS settings on your domain. This is required to send email.
 * ENCRYPTION_KEY - any 16 or 32 characters.

Your etc/environment file should end up having these lines:
```
MANDRILL_API_KEY='secret'
SECRET_KEY='secret'
DOMAIN_NAME='www.yourdomain.com'
ENCRYPTION_KEY='1111111111111111'
GOOGLE_CUSTOMER_KEY='secret'
GOOGLE_CUSTOMER_SECRET='secret'
MEETUP_CUSTOMER_KEY='secret'
MEETUP_CUSTOMER_SECRET='secret'

```

### Setup For Production
* Set environmental variables on heroku:
 * heroku config:add PRODUCTION_SETTINGS='production_settings.py' MANDRILL_API_KEY='secret' SECRET_KEY='secret' DOMAIN_NAME='www.yourdomain.com' ENCRYPTION_KEY='secret' GOOGLE_CUSTOMER_KEY='secret' GOOGLE_CUSTOMER_SECRET='secret' MEETUP_CUSTOMER_KEY='secret' MEETUP_CUSTOMER_SECRET='secret'
  * heroku config:set PYTHONPATH='fakepath'
* https://github.com/albertogg/flask-bootstrap-skel#production-configuration

### TODO
* Add meetup support.
