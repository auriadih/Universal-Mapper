"""
PRELIMINARY LIBRARIES AND CONFIGURATION
"""

# import Flask classes
from flask import redirect, render_template, url_for
from flask import request, jsonify
from flask import session

# import login functions
from flask_login import login_required, current_user

# import RESTful classes
from flask_restful import Api, Resource, fields, marshal, reqparse

# import all from /home
from . import browser

# import database settings and classes
from .. import db
from ..models import User, Organisations
from ..models import CodeSystem, Dialect, VDialect
from ..models import Terms, Codes, Concepts, ConceptMetadata, Comments
from ..models import VConcepts
from ..models import Mapping, VMapping
from ..models import default_query
from sqlalchemy import func, exc, literal, cast, and_, or_, not_, inspect
from sqlalchemy.orm import aliased
from sqlalchemy.types import DateTime as dt

# import variable functions and formats
import time, datetime
import decimal
import collections
from collections import OrderedDict
import re

# import downloading functions
import urllib.request, json
import requests # POSTing to server

# server-side processing
from .serverside_table import ServerSideTable
from . import server_columns






"""
HOMEPAGE
"""

# route home page to '/' handle
@browser.route('/')

def homepage():
	if current_user.is_authenticated:
		# check if user has default dialects
		user_dialects = db.session.query(User)\
			.filter((User.user_id == session['user_id'])
				& (User.default_source_dialect_id != None)
				& (User.default_destination_dialect_id != None))\
			.subquery()

		# set session variables if default systems are set for user
		if db.session.query(user_dialects).count() == 1:
			# source system info
			user_source_system = db.session.query(VDialect)\
				.filter(VDialect.dialect_id == user_dialects.c.default_source_dialect_id)\
				.first()

			# target system info
			user_destination_system = db.session.query(VDialect)\
				.filter(VDialect.dialect_id == user_dialects.c.default_destination_dialect_id)\
				.first()

			# session variables
			session['source_system'] = user_source_system.code_system_name
			session['source_system_id'] = user_source_system.code_system_id
			session['source_dialect'] = user_source_system.dialect_name
			session['source_dialect_id'] = user_source_system.dialect_id
			session['target_system'] = user_destination_system.code_system_name
			session['target_system_id'] = user_destination_system.code_system_id
			session['target_dialect'] = user_destination_system.dialect_name
			session['target_dialect_id'] = user_destination_system.dialect_id

			# redirect to mapper page
			return redirect(url_for('browser.mapper_panel'))

		else:
			# redirect to code system selection page
			return redirect(url_for('browser.select_codesystem'))

	else:
		# render home page for visitors
		return render_template('home/index.html')






"""
CODE SYSTEM TO MAP
"""

@browser.route('/code_systems')

# user cannot access this page without logging in
@login_required

def select_codesystem():
	# find out which code systems are available for the logged in user
	source_systems = db.session.query(VConcepts)\
		.filter(VConcepts.organisation_id == session['user_organisation'])\
		.distinct(VConcepts.code_system_name,
			VConcepts.code_system_owner_organisation_name,
			VConcepts.organisation_name,
			VConcepts.dialect_name,
			VConcepts.code_system_id)\
		.with_entities(VConcepts.code_system_name,
			VConcepts.code_system_owner_organisation_name,
			VConcepts.organisation_name,
			VConcepts.dialect_name,
			VConcepts.code_system_id)\
		.order_by(VConcepts.code_system_id)\
		.all()

	return render_template('home/select.html',
		user_org_name = session['user_organisation_name'],
		source_systems = source_systems)






# class to determine which code systems are displayed to user
@browser.route('/_code_systems', methods = ['POST'])

def return_codesystems():
	btn = eval(request.form['b'])

	# set session variables to retain selected code systems based on buttons clicked
	session['source_system'] = btn[0]
	session['source_system_id'] = db.session.query(CodeSystem)\
		.filter(CodeSystem.name == btn[0])\
		.with_entities(CodeSystem.code_system_id)\
		.scalar()

	session['source_dialect'] = btn[2]
	session['source_dialect_id'] = db.session.query(Dialect)\
		.filter(Dialect.dialect_name == btn[3])\
		.with_entities(Dialect.dialect_id)\
		.scalar()

	# return code system information based on buttons clicked
	systems = db.session.query(CodeSystem, Dialect, Organisations)\
		.join(Dialect, Dialect.code_system_id == CodeSystem.code_system_id)\
		.join(Organisations, Organisations.organisation_id == CodeSystem.owner_organisation_id)\
		.filter(((CodeSystem.name != btn[0])
			| (Dialect.dialect_name != btn[3])
			| (Organisations.name != btn[1]))
			& (Dialect.is_official == True))\
		.with_entities(CodeSystem.name,
			Organisations.name,
			Dialect.dialect_name,
			CodeSystem.code_system_id)\
		.order_by(CodeSystem.code_system_id)\
		.all()

	return(jsonify(systems))






# class to save chosen target code system to session variable
@browser.route('/_target_system', methods = ['POST'])

def save_target_codesystem():
	btn = eval(request.form['b'])

	# set session variables to retain selected code systems based on buttons clicked
	session['target_system'] = btn[0]
	session['target_system_id'] = db.session.query(CodeSystem)\
		.filter(CodeSystem.name == btn[0])\
		.with_entities(CodeSystem.code_system_id)\
		.scalar()

	session['target_dialect'] = btn[2]
	session['target_dialect_id'] = db.session.query(Dialect)\
		.filter(Dialect.dialect_name == btn[2])\
		.with_entities(Dialect.dialect_id)\
		.scalar()

	# update default systems to db user table
	db.session.query(User)\
		.filter(User.user_id == session['user_id'])\
		.update({ 'default_source_dialect_id': session['source_dialect_id'] })
	db.session.query(User)\
		.filter(User.user_id == session['user_id'])\
		.update({ 'default_destination_dialect_id': session['target_dialect_id'] })
	db.session.commit()

	# redirect to mapper page
	return url_for('browser.mapper_panel')






"""
CODE MAPPING PANEL
"""

@browser.route('/terms')

# user cannot access this page without logging in
@login_required

def mapper_panel():
	if current_user.is_authenticated:
		return render_template('home/terms.html',
			user_org_name = session['user_organisation_name'])

	else:
		# if not authenticated, return to login page
		return redirect(url_for('auth.login'))






# class to retrieve desired columns from database using custom db function
@browser.route('/_terms', methods = ['POST'])

def mapper_terms():
	# use bare SQL to fetch the table that custom db function is returning
	res = db.engine.execute(default_query.query('select') + default_query.query('from') + ';')

	# return interactive DataTable.js data table
	cols = server_columns.returned_columns_from_server
	return(jsonify(ServerSideTable(request, res, cols).output_result()))






# class to retrieve current progress of mappings
@browser.route('/_pbar', methods = ['GET'])

def mapper_progress():
	# user bare SQL to fetch the aggregated result of the table that custom db function is returning
	sel = 'select status as status, count(*) as term_counts, sum(obs_number) as samp_counts'
	grp = ' group by status'
	cnt = db.engine.execute(sel + default_query.query('from') + grp + ';')
	res = cnt.fetchall()

	res_fields = {
		'status': fields.String,
		'term_counts': fields.Integer,
		'samp_counts': fields.Integer
	}
	return(jsonify(data = marshal(res, res_fields)))






# class for adding a note for certain concept
@browser.route('/add_note/<concept_id>', methods = ['GET'])

def concept_note(concept_id):
	concept_info = db.session.query(VConcepts)\
		.filter(VConcepts.concept_id == concept_id)\
		.with_entities(VConcepts.code_text,
			VConcepts.term_text,
			VConcepts.obs_number)\
		.all()
	
	old_note = db.session.query(Comments)\
		.filter((Comments.user_id == session['user_id'])
			& (Comments.concept_id == concept_id))\
		.with_entities(Comments.note)\
		.first()

	return render_template('home/comment.html',
		info = concept_info,
		note_text = old_note.note if old_note is not None else '',
		user_org_name = session['user_organisation_name'])






# commenting concepts
@browser.route('/_commenting', methods = ['POST'])

def handle_comments():
	try:
		# find out what concept is being commented based on the url of the page (see previous route)
		concept_id = int(request.referrer.split('/')[-1])
	except:
		return "something went wrong", 406

	try:
		# add comment to database
		db.session.query(func.code_mapper.upsert_user_concept_note(
			session['user_id'],
			concept_id,
			request.form['comment'])).scalar()
		db.session.commit()
		db.session.close()
		return 'successfully written to database', 201

	except exc.SQLAlchemyError:
		return 'something went wrong', 500






"""
MAPPING
"""

@browser.route('/novel_terms/<concept_id>', methods = ['GET'])

# user cannot access this page without logging in
@login_required

def mapper_novels(concept_id):
	# subquery for searching for mapped concepts and returning concept details
	concept_info = db.session.query(VConcepts)\
		.filter(VConcepts.concept_id == concept_id)\
		.subquery()

	# CTE for limiting returned mappings
	maps = db.session.query(VMapping)\
		.filter((VMapping.source_code_system_id == session['source_system_id'])
			& (VMapping.destination_code_system_id == session['target_system_id']))\
		.cte('maps')

	# check from previous mappings of other organisations and bridge for similar concepts
	possible_mappings = db.session.query(VMapping)\
		.filter((maps.c.destination_code_text != '')
			& ((maps.c.source_code_text == concept_info.c.code_text)
			| (maps.c.source_term_text == concept_info.c.term_text)))\
		.with_entities(maps.c.destination_code_text,
			maps.c.destination_term_text,
			maps.c.destination_dialect_name,
			maps.c.organisation_name,
			maps.c.destination_concept_id)\
		.distinct(maps.c.destination_code_text,
			maps.c.destination_term_text,
			maps.c.organisation_name,
			maps.c.destination_dialect_name)\
		.all()

	# concept details to front-end (novel_terms)
	concept_decoded = db.session.query(concept_info)\
		.filter(VConcepts.concept_id == concept_id)\
		.with_entities(VConcepts.code_text,
			VConcepts.term_text,
			VConcepts.obs_number)\
		.all()

	return render_template('home/novel.html',
		info = concept_decoded,
		data = possible_mappings,
		target = session['target_system'],
		user_org_name = session['user_organisation_name'])






@browser.route('/propositions/<concept_id>', methods = ['GET'])

# user cannot access this page without logging in
@login_required

def mapper_propositions(concept_id):
	# subquery for searching for mapped concepts and returning concept details
	concept_info = db.session.query(VConcepts)\
		.filter(VConcepts.concept_id == concept_id)\
		.subquery()
	
	# CTE for limiting returned mappings
	maps = db.session.query(VMapping)\
		.filter((VMapping.source_code_system_id == session['source_system_id'])
			& (VMapping.destination_code_system_id == session['target_system_id']))\
		.cte('maps')

	# check from previous mappings of other organisations and bridge for similar concepts
	possible_mappings = db.session.query(VMapping)\
		.filter((maps.c.destination_code_text != '')
			& ((func.upper(maps.c.source_code_text) == func.upper(concept_info.c.code_text))
			& (func.upper(maps.c.source_term_text) == func.upper(concept_info.c.term_text))))\
		.with_entities(maps.c.source_code_text,
			maps.c.source_term_text,
			maps.c.destination_code_text,
			maps.c.destination_term_text,
			maps.c.destination_dialect_name,
			maps.c.organisation_name,
			maps.c.destination_concept_id)\
		.distinct(maps.c.destination_code_text,
			maps.c.destination_term_text,
			maps.c.destination_dialect_name)\
		.all()
	
	# concept details to front-end (propositions)
	concept_decoded = db.session.query(concept_info)\
		.filter(VConcepts.concept_id == concept_id)\
		.with_entities(VConcepts.code_text,
			VConcepts.term_text,
			VConcepts.obs_number)\
		.all()

	return render_template('home/propositions.html',
		info = concept_decoded,
		data = possible_mappings,
		target = session['target_system'],
		user_org_name = session['user_organisation_name'])






# class to retrieve desired columns from database using custom db function
@browser.route('/_similar_terms', methods = ['POST'])

def similar_terms():
	# find out if user came from right subpage and what was the viewed concept
	ref = re.split('\/|\?', request.referrer)
	suit = ['propositions', 'novel_terms']
	i = [ref.index(x) for x in ref if x in suit][0]
	concept_id = int(ref[i + 1])

	# concept details for 'where' clause in bare SQL
	conc = db.session.query(VConcepts)\
		.filter(VConcepts.concept_id == concept_id)\
		.first()

	wh = " where (code_text = '" + str(conc.code_text) + "' OR term_text = '" + str(conc.term_text) + "') "\
		+ "and not (code_text = '" + str(conc.code_text) + "' AND term_text = '" + str(conc.term_text) + "')"
	res = db.engine.execute(default_query.query('select') + default_query.query('from') + wh + ';')

	# return interactive DataTable.js data table
	cols = server_columns.returned_columns_from_server
	return(jsonify(ServerSideTable(request, res, cols).output_result()))






# mapper functions to save mapped terms to database
@browser.route('/_event', methods = ['POST'])

def concept_mapper():
	# gather all concepts to be mapped
	concepts = []

	try:
		ref = re.split('\/|\?', request.referrer)
		suit = ['propositions', 'novel_terms']
		i = [ref.index(x) for x in ref if x in suit][0]
		concept_id = int(ref[i + 1])
		concepts.append(concept_id)
	except:
		return 'something went wrong', 406

	# if multiple source concepts are selected to be mapped to novel concept, form a loop
	old_concepts = request.form.getlist('old_concepts[]')
	if old_concepts:
		concepts.extend(old_concepts)

	# loop all concepts to be mapped
	for concept in concepts:
		new_code = request.form.get('new_code')
		new_term = request.form.get('new_term')
		comment = request.form.get('comment')

		# if no novel concept is given, then mark original concept as rejected
		if new_code == None and new_term == None:
			reason = 'Incorrect concept'
		else:
			reason = 'User mapping'

		try:
			# use db function to check if new code & term concept is present
			if new_code == None and new_term == None:
				new_concept = None
			else:
				owner_id = db.session.query(CodeSystem)\
					.filter(CodeSystem.code_system_id == session['target_system_id'])\
					.with_entities(CodeSystem.owner_organisation_id)\
					.scalar()

				new_concept = db.session.query(func.code_mapper.insert_concept_if_not_exists(
					new_code,
				    new_term,
				    owner_id, # session['user_organisation']
				    session['target_dialect_id'])).scalar()
				db.session.commit()

			# add event
			mapping = db.session.query(func.code_mapper.insert_mapping(
		    	session['user_id'],
		    	session['session_id'],
		    	reason,
		    	concept,
		    	new_concept,
		    	session['target_dialect_id'],
				comment)).scalar()
			db.session.commit()

		except exc.SQLAlchemyError:
			return 'something went wrong', 500

	db.session.close()
	return 'successfully written to database', 201






# info about mapped concept
@browser.route('/details/<concept_id>', methods = ['GET'])

# user cannot access this page without logging in
@login_required

def mapper_details(concept_id):
	# subquery for searching for mapped concepts and returning concept details
	concept_info = db.session.query(VConcepts)\
		.filter(VConcepts.concept_id == concept_id)\
		.subquery()

	# mapping history
	hist = db.session.query(VMapping)\
		.filter((VMapping.source_concept_id == concept_id)
			& (VMapping.valid == True))\
		.subquery()

	concept_history = db.session.query(hist)\
		.with_entities(hist.c.valid,
			func.concat(hist.c.last_name, ', ', func.substr(hist.c.first_name,1,1), ' (', hist.c.organisation_name, ')').label('mapper'),
			hist.c.destination_code_text,
			hist.c.destination_term_text,
			hist.c.event_type_name,
			func.coalesce(hist.c.comment, '').label('comment'),
			func.to_char(hist.c.insert_ts, 'YYYY-mm-dd HH24:MI').label('insert_ts'))\
		.order_by(hist.c.insert_ts.desc())\
		.all()

	# other source concepts to same destination concept
	other_concepts = db.session.query(VMapping)\
		.filter((VMapping.destination_concept_id == hist.c.destination_concept_id)
			& (VMapping.valid == True))\
		.with_entities(VMapping.valid,
			func.concat(VMapping.last_name, ', ', func.substr(VMapping.first_name,1,1), ' (', VMapping.organisation_name, ')').label('mapper'),
			VMapping.source_code_text,
			VMapping.source_term_text,
			VMapping.event_type_name,
			func.coalesce(VMapping.comment, '').label('comment'),
			func.to_char(VMapping.insert_ts, 'YYYY-mm-dd HH24:MI').label('insert_ts'))\
		.order_by(VMapping.insert_ts.desc())\
		.all()

	# concept details to front-end (details)
	concept_decoded = db.session.query(concept_info)\
		.filter(VConcepts.concept_id == concept_id)\
		.with_entities(VConcepts.code_text,
			VConcepts.term_text,
			VConcepts.obs_number)\
		.all()

	return render_template('home/details.html',
		history = concept_history,
		samedest = other_concepts,
		info = concept_decoded,
		target = session['target_system'],
		user_org_name = session['user_organisation_name'])






"""
EMBEDDED EXTERNAL CONTENT
"""

@browser.route('/_api_fetcher', methods = ['POST'])

def download_data():
	# what sub-url of API
	httplink = request.form['urli']

	# if POST from front-end includes arguments, pass them as payload
	if 'args' in request.form:
		payload = request.form['args']
		r = requests.post(httplink, data = json.loads(payload))
		return(jsonify(r.json()))

	# if POST from front-end without arguments, make ordinary GET
	else:
		with urllib.request.urlopen(httplink) as url:
			stringed = url.read().decode('utf-8')
			json_obj = json.loads(stringed)
			return(jsonify(json_obj))






"""
MAPPING STATISTICS
"""

@browser.route('/tilastot')

# user cannot access this page without logging in
@login_required

def stats():
	# already mapped (all)
	snomapped = Mapping.query\
		.distinct(Mapping.mapping_id)\
		.with_entities(Mapping.code_text,
			Mapping.term_text)\
		.all()

	snomedmapped = collections.OrderedDict(snomapped)

	# render home page for authenticated users
	return render_template('home/tilastot.html',
		mapped = jsonify(snomedmapped))
