Calendar Admin
---

Calendar Admin adds the ability to send requests to the administrators of your Google Calendar to have events added. 

It allows you to generate a link to use for an "Add Event" button above your calendar, so your users can request to have events added to your calendar.

![Alt text](https://github.com/pawl/CalendarAdmin/blob/master/screenshots/add_event.png "Add Event Button")

The user is taken to an event request form, which is approved or denied by calendar administrators once it is submitted:

![Alt text](https://github.com/pawl/CalendarAdmin/blob/master/screenshots/event_request_form.png "Request Form")


### Project Facts
* Uses Python's Flask Web Framework with the Flask-Admin extension.
* Project is designed to be deployed on Heroku, but can be run locally (preferrably an Ubuntu/Debian server) by using "fab run".
* Uses SQLAlchemy (Flask-SQLAlchemy) as the ORM. Locally it uses SQLite, on Heroku it uses Postgres.
* OAUTH authentication made easier by Authomatic.
* Used https://github.com/albertogg/flask-bootstrap-skel for initial boilerplate.
* Admin interface is using the SB Admin 2 theme: http://startbootstrap.com/template-overviews/sb-admin-2/
* Email is handled using Mandrill.
* Alembic is used for database migrations.
* Uses Imgur's API for hosting location images and resizing. Thanks Imgur!

### Additional Facts About Database
* The models for the database tables are here: https://github.com/pawl/CalendarAdmin/blob/master/application/models.py
* The database tables are generated during the setup instructions (based on the models).
* You will need to be familiar with SQLAlchemy.
  * This guide is helpful for understanding how SQLAlchemy is used: https://pythonhosted.org/Flask-SQLAlchemy/queries.html
  * This guide is helpful for understanding relations: http://docs.sqlalchemy.org/en/rel_0_9/orm/relationships.html

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
 * IMGUR_ID - Register your application with Imgur to post anonymously. You just need the client_id. This is for the images of locations.
 * ENCRYPTION_KEY - any 16 or 32 characters.
5. To get image processing working for the locations view, you may need to apt-get some additional libraries: http://askubuntu.com/a/272095

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
IMGUR_ID='aaaaaaaaaaaaaaa'
```

### Setup For Production
* Set environmental variables on heroku:
 * heroku config:add PRODUCTION_SETTINGS='production_settings.py' MANDRILL_API_KEY='secret' SECRET_KEY='secret' DOMAIN_NAME='www.yourdomain.com' ENCRYPTION_KEY='secret' GOOGLE_CUSTOMER_KEY='secret' GOOGLE_CUSTOMER_SECRET='secret' MEETUP_CUSTOMER_KEY='secret' MEETUP_CUSTOMER_SECRET='secret' IMGUR_ID='aaaaaaaaaaaaaaa'
  * heroku config:set PYTHONPATH='fakepath'
* https://github.com/albertogg/flask-bootstrap-skel#production-configuration

### TODO
* Add meetup support.
* Add eventbrite support.
* Improve styling on front page.
* Improve styling on requests page.
* Write unit test for requesting an event.
* Allow scheduling repeating classes (need to be careful not to let classes run indefinitely).
* Make the admin interface more user friendly by adding a more obvious button to create public urls for calendars.
