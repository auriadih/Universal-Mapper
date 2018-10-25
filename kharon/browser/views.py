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
from ..models import CodeSystem, Dialect
from ..models import Terms, Codes, Concepts, ConceptMetadata
from ..models import VConcepts
from ..models import Mapping, VMapping
from sqlalchemy import func, exc, literal, cast, and_, or_, not_, inspect
from sqlalchemy.orm import aliased

# import variable functions and formats
import time, datetime
import decimal
import collections
from collections import OrderedDict

# import downloading functions
import urllib.request, json
import requests # POSTing to server






"""
HOMEPAGE
"""

# route home page to '/' handle
@browser.route('/')

def homepage():
	if current_user.is_authenticated:
		# render home page for visitors
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

# user cannot access this page without logging in
@login_required

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

# user cannot access this page without logging in
@login_required

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

	return url_for('browser.mapper_panel')






"""
CODE MAPPING PANEL
"""

@browser.route('/mapper')

def mapper_panel():
	if current_user.is_authenticated:
		original_terms = db.session.query(VConcepts)\
			.filter((VConcepts.organisation_id == session['user_organisation'])\
				& (VConcepts.dialect_id == session['source_dialect_id'])\
				& (VConcepts.code_system_id == session['source_system_id']))\
			.with_entities(VConcepts.code_text.label('code_text'),
				VConcepts.term_text.label('term_text'),
				func.coalesce(VConcepts.obs_number, 1).label('obs_number'),
				VConcepts.first_obs_date.label('first_obs_date'),
				VConcepts.last_obs_date.label('last_obs_date'),
				VConcepts.concept_id.label('concept_id'))

		return render_template('home/panel.html',
			title = 'Universal Mapper',
			source = session['source_system'],
			target = session['target_system'],
			user_id = session['user_id'],
			user_org = session['user_organisation'],
			originals = original_terms)

	else:
		# if not authenticated, return to login page
		return redirect(url_for('auth.login'))






"""
MAPPING
"""

# fuzzy match original term to novel term and pass results to page
@browser.route('/_fuzzymatch', methods = ['POST'])

# user cannot access this page without logging in
@login_required

def fuzzymatch():
	mappings_cte = db.session.query(VMapping)\
		.filter((VMapping.source_code_system_id == session['source_system_id'])\
			& (VMapping.destination_code_system_id == session['target_system_id']))\
		.cte("mappings_cte")

	possible_mappings = db.session.query(mappings_cte)\
		.filter((mappings_cte.c.destination_code_text != "")\
			& ((mappings_cte.c.source_code_text == request.form['code'])\
			| (mappings_cte.c.source_term_text == request.form['desc'])))\
		.with_entities(mappings_cte.c.source_code_text,
			mappings_cte.c.source_term_text,
			mappings_cte.c.source_dialect_name,
			mappings_cte.c.source_concept_id,
			mappings_cte.c.destination_code_text,
			mappings_cte.c.destination_term_text,
			mappings_cte.c.destination_dialect_name,
			mappings_cte.c.destination_concept_id)\
		.all()

	return(jsonify(matched = possible_mappings))






@browser.route('/_checker', methods = ['GET'])

# user cannot access this page without logging in
@login_required

def check_mapped_terms():
	def append_results(to):
		to.append(OrderedDict([('code_text', m.source_code_text), ('term_text', m.source_term_text)]))

	try:
		base_mapping = db.session.query(VMapping)\
			.filter((VMapping.source_code_system_id == session['source_system_id'])\
				& (VMapping.valid == True))\
			.with_entities(VMapping.user_id,
				VMapping.organisation_id,
				VMapping.event_type_name,
				VMapping.source_code_text,
				VMapping.source_term_text,
				VMapping.source_dialect_id)\
			.all()

		um = []
		uom = []
		oom = []
		rc = []
		bc = []

		for m in base_mapping:
			if m.user_id == session['user_id'] and \
				m.event_type_name == "User mapping":
				append_results(um)
			elif m.organisation_id == session['user_organisation'] and \
				m.event_type_name == "User mapping":
				append_results(uom)
			elif m.organisation_id != session['user_organisation'] and \
				m.event_type_name == "User mapping":
				append_results(oom)
			elif m.organisation_id == session['user_organisation'] and \
				m.event_type_name == "Incorrect concept" and \
				m.source_dialect_id == session['source_dialect_id']:
				append_results(rc)
			elif m.event_type_name == "Bridge mapping":
				append_results(bc)

		l = []
		l.append(um)
		l.append(uom)
		l.append(oom)
		l.append(rc)
		l.append(bc)

		return(jsonify(l))

	except:
		empty = 0
		return(jsonify(empty))






@browser.route('/_other_mapped', methods = ['POST'])

# user cannot access this page without logging in
@login_required

def check_mapped_concepts():
	try:
		mapped_concepts = db.session.query(VMapping)\
			.filter((VMapping.source_code_system_id == session['source_system_id'])\
				& (VMapping.event_type_name == "User mapping")\
				& (VMapping.organisation_id != session['user_organisation'])\
				& ((func.upper(VMapping.source_code_text) == func.upper(request.form['code']))\
				& (func.upper(VMapping.source_term_text) == func.upper(request.form['desc']))))\
			.all()

		concept_fields = {
			'source_code_text': fields.String,
			'source_term_text': fields.String,
			'destination_code_text': fields.String,
			'destination_term_text': fields.String,
			'organisation_name': fields.String
		}

		return(jsonify(mapped = marshal(mapped_concepts, concept_fields)))

	except:
		empty = 0
		return(jsonify(empty))






@browser.route('/_autobridged', methods = ['POST'])

# user cannot access this page without logging in
@login_required

def check_bridged_concepts():
	try:
		bridged_concepts = db.session.query(VMapping)\
			.filter((VMapping.source_code_system_id == session['source_system_id'])\
				& (VMapping.event_type_name == "Bridge mapping")\
				& ((func.upper(VMapping.source_code_text) == func.upper(request.form['code']))\
				& (func.upper(VMapping.source_term_text) == func.upper(request.form['desc']))))\
			.all()

		similar_concepts = db.session.query(VConcepts, VMapping)\
			.outerjoin(VMapping, and_(func.upper(VMapping.source_code_text) == func.upper(request.form['code']),\
				func.upper(VMapping.source_term_text) == func.upper(request.form['desc']),\
				or_(func.upper(VMapping.source_code_text) == func.upper(VConcepts.code_text),\
				func.upper(VMapping.source_term_text) == func.upper(VConcepts.term_text)),\
				VMapping.source_code_system_id == VConcepts.code_system_id))\
			.filter((VConcepts.code_system_id == session['source_system_id'])\
				& (VMapping.event_type_name == "Bridge mapping")\
				& (VConcepts.organisation_id == session['user_organisation'])\
				& ((func.upper(VConcepts.code_text) == func.upper(request.form['code']))\
				| (func.upper(VConcepts.term_text) == func.upper(request.form['desc']))))\
			.all()

		sc = []
		for result in similar_concepts:
			sc.append(OrderedDict([('code_text', result[0].code_text),
				('term_text', result[0].term_text),
				('obs_number', result[0].obs_number),
				('destination_code_text', result[1].destination_code_text),
				('destination_term_text', result[1].destination_term_text)]))

		concept_fields = {
			'source_code_text': fields.String,
			'source_term_text': fields.String,
			'obs_number': fields.String,
			'destination_code_text': fields.String,
			'destination_term_text': fields.String
		}

		return(jsonify(bridged = marshal(bridged_concepts, concept_fields),
			similar = sc))

	except:
		empty = 0
		return(jsonify(empty))






@browser.route('/_similars', methods = ['POST'])

# user cannot access this page without logging in
@login_required

def check_similar_concepts():
	similar_concepts = db.session.query(VConcepts)\
		.filter((VConcepts.code_system_id == session['source_system_id'])\
			& (VConcepts.organisation_id == session['user_organisation'])\
			& not_((VConcepts.code_text == request.form['code'])\
			& (VConcepts.term_text == request.form['desc']))\
			& ((func.upper(VConcepts.code_text) == func.upper(request.form['code']))\
			| (func.upper(VConcepts.term_text) == func.upper(request.form['desc']))))\
		.all()

	concept_fields = {
		'code_text': fields.String,
		'term_text': fields.String,
		'obs_number': fields.String
	}

	return(jsonify(similar = marshal(similar_concepts, concept_fields)))






# mapper functions to save mapped terms to database
@browser.route('/_event', methods = ['POST'])

# user cannot access this page without logging in
@login_required

def concept_mapper():
	old_code = request.form.get('old_code')
	old_term = request.form.get('old_term')
	new_code = request.form.get('new_code')
	new_term = request.form.get('new_term')
	comment = request.form.get('comment')

	if new_code == None and new_term == None:
		reason = "Incorrect concept"
	else:
		reason = "User mapping"

	try:
		# get concept ID for old code and old term
		old_concepts = db.session.query(VConcepts)\
			.filter((VConcepts.organisation_id == session['user_organisation'])\
				& (VConcepts.code_system_id == session['source_system_id'])\
				& (VConcepts.dialect_id == session['source_dialect_id'])\
				& (VConcepts.code_text == old_code)\
				& (VConcepts.term_text == old_term))\
			.with_entities(VConcepts.concept_id)\
			.distinct(VConcepts.concept_id)\
			.all()

		# use db function to check if new code & term concept is present
		if new_code == None and new_term == None:
			new_concept = None
		else:
			new_concept = db.session.query(func.code_mapper.insert_concept_if_not_exists(
				new_code,
			    new_term,
			    session['user_organisation'],
			    session['target_dialect_id'])).scalar()
			db.session.commit()

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
				db.session.commit()

			return "successfully written to database", 201

		except exc.SQLAlchemyError:
			return "something went wrong", 500

	except exc.SQLAlchemyError:
		return "something went wrong", 500






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
			& (VMapping.source_dialect_id == session['source_dialect_id'])\
			& ((VMapping.destination_code_system_id == session['target_system_id'])\
			| (VMapping.destination_code_system_id == None))\
			& ((VMapping.destination_dialect_id == session['target_dialect_id'])
			| (VMapping.destination_dialect_id == None)))\
		.with_entities(VMapping.valid,
			VMapping.username,
			VMapping.last_name,
			VMapping.first_name,
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
			VMapping.insert_ts,
			VMapping.update_ts)\
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
			& (VMapping.valid == False))\
		.with_entities(VMapping.valid,
			VMapping.username,
			VMapping.last_name,
			VMapping.first_name,
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






"""
BORROWED FROM OTHER PROJECT

# search-as-you-type functionality for lab tests
@browser.route('/_lab_autocomplete', methods=['GET'])

# user cannot access this page without logging in
@login_required

def autocomplete():
	search = request.args.get('q')
	ltests = LabCheck.query\
		.filter((func.upper(LabCheck.test).like(func.upper('%' + str(search) + '%')))\
		& (LabCheck.patient_id == session['patient_id']))\
        .distinct(LabCheck.test)\
		.with_entities(LabCheck.test, LabCheck.unit)\
		.all()
	return(jsonify(ltests))

lab_fields = {
	'result': fields.String,
	'unit': fields.String,
	'start_ts': fields.DateTime(dt_format='iso8601'),
	'patient_id': fields.Integer
}

# lab values
@browser.route('/_hae_labratiedot', methods=['POST'])

# user cannot access this page without logging in
@login_required

def labarvot():
	selected_lab_test = request.form.to_dict()
	lresults = LabCheck.query\
		.filter((selected_lab_test['ltest'] == LabCheck.test + " (" + LabCheck.unit + ")")\
		& (LabCheck.patient_id == session['patient_id']))\
		.with_entities(LabCheck.result, LabCheck.start_ts)
	print(lresults.all())
	return(jsonify(lresults.all()))
"""
