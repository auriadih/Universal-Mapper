"""
PRELIMINARY LIBRARIES AND CONFIGURATION
"""

# import necessary libraries
from flask import redirect, render_template, url_for
from flask import request, jsonify, json
from flask import Blueprint
from flask import session
from flask import flash

# import login library
from flask_login import login_required, login_user, logout_user, current_user
from . import tunnistautuminen

# make session permanent; it would be cleared only on logout
@tunnistautuminen.before_request
def session_management():
	session.permanent = True

# import necessary forms
from .forms import LoginForm, RegistrationForm
from wtforms.fields import *
from wtforms import validators

# import database connection classes
from .. import db
from ..models import User, Session, Organisations
from sqlalchemy import *

# import date functions
import time, datetime

# import RESTful classes
from flask_restful import Api, Resource, fields, marshal, reqparse

# define function to get current time
def curTime():
	return(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))






"""
USER ACCOUNT FUNCTIONALITY
"""

# route registration page with GET and POST allowed
@tunnistautuminen.route('/register', methods = ['GET', 'POST'])

def register():
	# summon registration form
	form = RegistrationForm()

	if form.validate_on_submit():
		org_id = db.session.query(Organisations)\
			.filter(Organisations.name == form.organisation.data)\
			.with_entities(Organisations.organisation_id)\
			.scalar()

		# collect user info from the form using User() data format from 'models'
		user = User(email = form.email.data,
			organisation_id = org_id,
			username = form.username.data,
			first_name = form.first_name.data,
			last_name = form.last_name.data,
			password = form.password.data)

		# submit registration info to database
		db.session.add(user)
		db.session.commit()

		# redirect to the login page
		return redirect(url_for('auth.login'))

	# load registration template
	return render_template('auth/register.html', reg = form, title = 'Rekisteröidy')






# route login page with GET and POST allowed
@tunnistautuminen.route('/login', methods = ['GET', 'POST'])

def login():
	# summon login form
	form = LoginForm()

	if form.validate_on_submit():
		# check user is in the database
		user = User.query.filter_by(email = form.email.data).first()

		# check 'user' is not empty and users password is correct
		if user is not None and user.verify_password(form.password.data):
			# log user in
			login_user(user)

			session['user_id'] = int(current_user.get_id())

			# find out which organisation user belongs to
			session['user_organisation'] = db.session.query(User, Organisations)\
				.join(Organisations, Organisations.organisation_id == User.organisation_id)\
				.filter(User.user_id == session['user_id'])\
				.with_entities(Organisations.organisation_id)\
				.scalar()
			session['user_organisation_name'] = db.session.query(User, Organisations)\
				.join(Organisations, Organisations.organisation_id == User.organisation_id)\
				.filter(User.user_id == session['user_id'])\
				.with_entities(Organisations.name)\
				.scalar()

			# add row to database using Session() db model
			ses_start = curTime()
			ses = Session(user_id = session['user_id'],
				start_ts = ses_start)
			db.session.add(ses)
			db.session.commit()

			# collect necessary information about current session
			cur_ses = Session.query\
				.filter((Session.user_id == session['user_id'])\
				& (Session.start_ts == ses_start))\
				.with_entities(Session.session_id)\
				.scalar()

			session['session_id'] = cur_ses

			# redirect to the dashboard page after login
			return redirect(url_for('browser.homepage'))

			# when login details are incorrect
		else:
			flash('Väärä käyttäjätunnus tai salasana!')
			return redirect(url_for('auth.login'))

	# load login template
	return render_template('auth/login.html', login = form, title = 'Kirjaudu sisään')






# route logout page
@tunnistautuminen.route('/logout', methods = ['GET', 'POST'])

# in order to enter logout page, user have to be logged in first
@login_required

# define logout request
def logout():
	# log user out
	logout_user()

	# add timestamp to database for closing session
	end_ses = db.session.query(Session)\
		.filter(Session.session_id == session['session_id'])\
		.update({ "end_ts": (curTime()) })
	db.session.commit()

	# end session (empty global 'session' variable)
	session.clear()

	# redirect to homepage
	return redirect(url_for('browser.homepage'))
