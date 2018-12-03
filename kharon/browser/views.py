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
				.with_entities(VDialect.code_system_name,
					VDialect.code_system_id,
					VDialect.dialect_name,
					VDialect.dialect_id)\
				.all()

			# target system info
			user_destination_system = db.session.query(VDialect)\
				.filter(VDialect.dialect_id == user_dialects.c.default_destination_dialect_id)\
				.with_entities(VDialect.code_system_name,
					VDialect.code_system_id,
					VDialect.dialect_name,
					VDialect.dialect_id)\
				.all()

			# session variables
			session['source_system'] = user_source_system[0][0]
			session['source_system_id'] = user_source_system[0][1]
			session['source_dialect'] = user_source_system[0][2]
			session['source_dialect_id'] = user_source_system[0][3]
			session['target_system'] = user_destination_system[0][0]
			session['target_system_id'] = user_destination_system[0][1]
			session['target_dialect'] = user_destination_system[0][2]
			session['target_dialect_id'] = user_destination_system[0][3]

			# redirect to mapper page
			return redirect(url_for('browser.mapper_panel'))

		else:
			# redirect to code system selection page
			return redirect(url_for('browser.select_codesystem'))

	else:
		# render home page for visitors
		return render_template('home/index.html',
			title = 'Etusivu')






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
		title = 'Koodijärjestelmän valinta',
		source_systems = source_systems)






# class to determine which code systems are displayed to user
@browser.route('/_code_systems', methods = ['POST'])

def return_codesystems():
	btn = eval(request.form['b'])

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

	systems = db.session.query(CodeSystem, Dialect, Organisations)\
		.join(Dialect, Dialect.code_system_id == CodeSystem.code_system_id)\
		.join(Organisations, Organisations.organisation_id == CodeSystem.owner_organisation_id)\
		.filter(((CodeSystem.name != btn[0])\
			| (Dialect.dialect_name != btn[3])\
			| (Organisations.name != btn[1]))\
			& (Dialect.is_official == True))\
		.with_entities(CodeSystem.name,\
			Organisations.name,\
			Dialect.dialect_name,\
			CodeSystem.code_system_id)\
		.order_by(CodeSystem.code_system_id)\
		.all()

	return(jsonify(systems))






# class to save chosen target code system to session variable
@browser.route('/_target_system', methods = ['POST'])

def save_target_codesystem():
	btn = eval(request.form['b'])

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
			title = 'Universal Mapper: ' + session['source_system'],
			user_org_name = session['user_organisation_name'])

	else:
		# if not authenticated, return to login page
		return redirect(url_for('auth.login'))






# class to retrieve desired columns from database using custom db function
@browser.route('/_terms', methods = ['POST'])

def mapper_terms():
	#lim = " limit 100"
	res = db.engine.execute(default_query.query('select') + default_query.query('from') + ";") # + lim

	# interactive DataTable.js data table
	cols = server_columns.returned_columns_from_server
	return(jsonify(ServerSideTable(request, res, cols).output_result()))






# class for adding a note for certain concept
@browser.route('/add_note/<concept_id>', methods = ['GET'])

# user cannot access this page without logging in
@login_required

def concept_note(concept_id=0):
	concept_info = db.session.query(VConcepts)\
		.filter(VConcepts.concept_id == concept_id)\
		.with_entities(VConcepts.code_text,
			VConcepts.term_text,
			VConcepts.obs_number)\
		.all()

	return render_template('home/comment.html',
		info = concept_info,
		title = 'Universal Mapper: ' + session['source_system'],
		user_org_name = session['user_organisation_name'])






# commenting concepts
@browser.route('/_commenting', methods = ['POST'])

def handle_comments():
	try:
		concept_id = int(request.referrer.split("/")[-1])
	except:
		return "something went wrong", 406

	try:
		db.session.query(func.code_mapper.upsert_user_concept_note(session['user_id'], concept_id, request.form['comment'])).scalar()
		db.session.commit()
		db.session.close()
		return "successfully written to database", 201

	except exc.SQLAlchemyError:
		return "something went wrong", 500






"""
MAPPING
"""

@browser.route('/novel_terms/<concept_id>', methods = ['GET'])

# user cannot access this page without logging in
@login_required

def mapper_novels(concept_id):
	concept_info = db.session.query(VConcepts)\
		.filter(VConcepts.concept_id == concept_id)\
		.subquery()

	mappings_cte = db.session.query(VMapping)\
		.filter((VMapping.source_code_system_id == session['source_system_id'])\
			& (VMapping.destination_code_system_id == session['target_system_id']))\
		.cte("mappings_cte")

	possible_mappings = db.session.query(VMapping)\
		.filter((mappings_cte.c.destination_code_text != "")\
			& ((mappings_cte.c.source_code_text == concept_info.c.code_text)\
			| (mappings_cte.c.source_term_text == concept_info.c.term_text)))\
		.with_entities(mappings_cte.c.destination_code_text,
			mappings_cte.c.destination_term_text,
			mappings_cte.c.destination_dialect_name,
			mappings_cte.c.destination_concept_id)\
		.distinct(mappings_cte.c.destination_code_text,
			mappings_cte.c.destination_term_text,
			mappings_cte.c.destination_dialect_name)\
		.all()

	concept_decoded = db.session.query(concept_info)\
		.filter(VConcepts.concept_id == concept_id)\
		.with_entities(VConcepts.code_text,
			VConcepts.term_text,
			VConcepts.obs_number)\
		.all()

	return render_template('home/novel.html',
		info = concept_decoded,
		data = possible_mappings,
		#simi = similar_concepts,
		title = 'Universal Mapper: ' + session['target_system'],
		target = session['target_system'],
		user_org_name = session['user_organisation_name'])






# class to retrieve desired columns from database using custom db function
@browser.route('/_similar_terms', methods = ['POST'])

def similar_terms():
	try:
		ref = re.split("\/|\?", request.referrer)
		concept_id = int(ref[ref.index('novel_terms') + 1])
	except:
		return "something went wrong", 406

	concept_info = db.session.query(VConcepts)\
		.filter(VConcepts.concept_id == concept_id)\
		.with_entities(VConcepts.code_text,
			VConcepts.term_text,
			VConcepts.obs_number)\
		.all()

	#lim = " limit 100"
	wh = " where (code_text = '" + str(concept_info[0][0]) + "' OR term_text = '" + str(concept_info[0][1]) + "') and not (code_text = '" + str(concept_info[0][0]) + "' AND term_text = '" + str(concept_info[0][1]) + "')"
	res = db.engine.execute(default_query.query('select') + default_query.query('from') + wh + ";") # + lim

	# interactive DataTable.js data table
	cols = server_columns.returned_columns_from_server
	return(jsonify(ServerSideTable(request, res, cols).output_result()))






# mapper functions to save mapped terms to database
@browser.route('/_event', methods = ['POST'])

# user cannot access this page without logging in
#@login_required

def concept_mapper():
	concepts = []
	# check that user is coming from 'novel_terms' subpage
	try:
		ref = re.split("\/|\?", request.referrer)
		concepts = concepts.append(int(ref[ref.index('novel_terms') + 1]))
	except:
		return "something went wrong", 406

	# TODO: selvitä miten otetaan vastaan array ja loopataan
	old_concepts = request.form.get('old_concepts')
	if old_concepts:
		concepts = concepts.extend(old_concepts)
		concept_info = db.session.query(VConcepts)\
			.filter(VConcepts.concept_id == old_concept)\
			.with_entities(VConcepts.code_text,
				VConcepts.term_text)\
			.all()
	else:
		concept_info = db.session.query(VConcepts)\
			.filter(VConcepts.concept_id == concept_id)\
			.with_entities(VConcepts.code_text,
				VConcepts.term_text)\
			.all()

	old_code = concept_info[0][0]
	old_term = concept_info[0][1]
	new_code = request.form.get('new_code')
	new_term = request.form.get('new_term')
	comment = request.form.get('comment')
	undo = request.form.get('undo')

	if new_code == None and new_term == None and not undo:
		reason = "Incorrect concept"
	else:
		reason = "User mapping"

	try:
		# use db function to check if new code & term concept is present
		if new_code == None and new_term == None:
			new_concept = None
		else:
			new_concept = db.session.query(func.code_mapper.insert_concept_if_not_exists(
				new_code,
			    new_term,
			    session['user_organisation'],
			    session['target_dialect_id'])).scalar()

		# add event
		try:
			for old_concept in old_concepts:
				mapping = db.session.query(func.code_mapper.insert_mapping(
			    	session['user_id'],
			    	session['session_id'],
			    	reason,
			    	old_concept,
			    	new_concept,
			    	session['target_dialect_id'],
					comment)).scalar()

		except exc.SQLAlchemyError:
			return "something went wrong", 500


	except exc.SQLAlchemyError:
		return "something went wrong", 500

	finally:
		db.session.commit()
		db.session.close()
		return "successfully written to database", 201






# info about mapped concept
@browser.route('/_mapped_info', methods = ['POST'])

# user cannot access this page without logging in
@login_required

def mapper_info():
	mapped_code = request.form['code']
	mapped_term = request.form['desc']

	mapped_concept = db.session.query(VMapping)\
		.filter((VMapping.source_code_text == mapped_code)\
			& (VMapping.source_term_text == mapped_term)\
			& (VMapping.valid == True)\
			& (VMapping.source_code_system_id == session['source_system_id'])\
			& ((VMapping.destination_code_system_id == session['target_system_id']) | (VMapping.destination_code_system_id == None)))\
		.with_entities(VMapping.valid,
			VMapping.username,
			VMapping.last_name,
			func.substr(VMapping.first_name,1,1).label('first_name'),
			VMapping.organisation_name,
			VMapping.source_code_system_name,
			VMapping.source_dialect_name,
			VMapping.source_code_text,
			VMapping.source_term_text,
			VMapping.destination_code_system_name,
			VMapping.destination_dialect_name,
			VMapping.destination_code_text,
			VMapping.destination_term_text,
			VMapping.comment,
			func.to_char(VMapping.insert_ts, 'YYYY-mm-dd HH24:MI').label('insert_ts'),
			func.to_char(VMapping.update_ts, 'YYYY-mm-dd HH24:MI').label('update_ts'))\
		.all()

	target_concept = db.session.query(VMapping)\
		.filter((VMapping.source_code_text == mapped_code)\
			& (VMapping.source_term_text == mapped_term)\
			& (VMapping.valid == True)\
			& (VMapping.source_code_system_id == session['source_system_id'])\
			& (VMapping.source_dialect_id == session['source_dialect_id'])\
			& ((VMapping.destination_code_system_id == session['target_system_id'])\
			| (VMapping.destination_code_system_id == None))\
			& ((VMapping.destination_dialect_id == session['target_dialect_id'])
			| (VMapping.destination_dialect_id == None)))\
		.subquery()

	mapped_concept_history = db.session.query(VMapping)\
		.filter((((VMapping.destination_code_id == target_concept.c.destination_code_id)\
			& (VMapping.destination_term_id == target_concept.c.destination_term_id))
			| ((VMapping.source_code_id == target_concept.c.source_code_id)\
			& (VMapping.source_term_id == target_concept.c.source_term_id)))\
			& (VMapping.valid == False)
			& (VMapping.organisation_id == session['user_organisation']))\
		.with_entities(VMapping.valid,
			VMapping.username,
			VMapping.last_name,
			func.substr(VMapping.first_name,1,1).label('first_name'),
			VMapping.organisation_name,
			VMapping.source_code_system_name,
			VMapping.source_dialect_name,
			VMapping.source_code_text,
			VMapping.source_term_text,
			VMapping.destination_code_system_name,
			VMapping.destination_dialect_name,
			VMapping.destination_code_text,
			VMapping.destination_term_text,
			VMapping.comment,
			VMapping.event_type_name,
			VMapping.insert_ts,
			VMapping.update_ts)\
		.all()

	return(jsonify(mapd = mapped_concept, hist = mapped_concept_history))






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

def stats():
	if current_user.is_authenticated:
		# already mapped (all)
		snomapped = Mapping.query\
			.distinct(Mapping.mapping_id)\
			.with_entities(Mapping.code_text, Mapping.term_text)\
			.all()

		snomedmapped = collections.OrderedDict(snomapped)

		# render home page for authenticated users
		return render_template('home/tilastot.html',
			title = 'Mapper Statistics',
			mapped = jsonify(snomedmapped))

	else:
		# render home page for visitors
		return render_template('home/index.html',
			title = 'Etusivu')
