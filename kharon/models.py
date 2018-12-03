# import login library
from flask_login import UserMixin
from flask import session

# import password hash library
from werkzeug.security import generate_password_hash, check_password_hash

# import database connection handlers and login manager from local files
from kharon import db, login_manager
from sqlalchemy import ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

# schema name
martti = 'code_mapper'






# basic user table
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    user_id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(db.Integer)
    username = db.Column(db.String(60), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(60), index=True, unique=True)
    first_name = db.Column(db.String(60), index=True)
    last_name = db.Column(db.String(60), index=True)
    default_source_dialect_id = db.Column(db.Integer)
    default_destination_dialect_id = db.Column(db.Integer)

	# add property to prevent accessing password column
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

	# hash password
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

	# check hashed password matches plain-text password
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # customize get_id() to lookup user_id column (default name is 'id')
    def get_id(self):
        return int(self.user_id)

    def __repr__(self):
        return '<User: {} ({}) {} {}>'.format(self.username, self.user_id, self.first_name, self.last_name)






# organisations to be linked to users and concepts
class Organisations(db.Model):
    __tablename__ = 'organisation'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    organisation_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String)
    contact_user_id = db.Column(db.Integer)

    def __repr__(self):
        return '<Organisation: {} ({})>'.format(self.name, self.organisation_id)






# groups to be linked to users
class UserGroups(db.Model):
    __tablename__ = 'user_group'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    user_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, primary_key=True)
    insert_ts = db.Column(db.DateTime, server_default=func.now())
    update_ts = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Group: ({}) for User: ({})>'.format(self.group_id, self.user_id)






# group info
class Groups(db.Model):
    __tablename__ = 'group'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    group_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    insert_ts = db.Column(db.DateTime, server_default=func.now())
    update_ts = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Group: {} ({})>'.format(self.name, self.group_id)






# login user
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)






# keep track of user mapping sessions
class Session(db.Model):
    __tablename__ = 'session'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    session_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    start_ts = db.Column(db.DateTime, server_default=func.now())
    end_ts = db.Column(db.DateTime, onupdate=func.now())

    def update(self, session_ended_ts=None):
        if session_ended_ts:
            self.session_ended_ts = session_ended_ts

    def __repr__(self):
        return '<Session: {} for User: {}>'.format(self.session_id, self.user_id)






# table for used code systems
class CodeSystem(db.Model):
    __tablename__ = 'code_system'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    code_system_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    version = db.Column(db.String)
    owner_organisation_id = db.Column(db.Integer)
    insert_ts = db.Column(db.DateTime, server_default=func.now())
    update_ts = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Code System: {} {} ({}) from Organisation: {}>'.format(self.name, self.version, self.code_system_id, self.owner_organisation_id)






# suplementary code system info
class Dialect(db.Model):
    __tablename__ = 'dialect'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    dialect_id = db.Column(db.Integer, primary_key=True)
    code_system_id = db.Column(db.Integer)
    dialect_name = db.Column(db.String)
    is_official = db.Column(db.Boolean)
    insert_ts = db.Column(db.DateTime, server_default=func.now())
    update_ts = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Dialect: {} ({}) for Code System: {}>'.format(self.dialect_name, self.dialect_id, self.code_system_id)






# suplementary code system info (view)
class VDialect(db.Model):
    __tablename__ = 'v_dialect'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    dialect_id = db.Column(db.Integer, primary_key=True)
    dialect_name = db.Column(db.String)
    is_official = db.Column(db.Boolean)
    code_system_id = db.Column(db.Integer)
    code_system_name = db.Column(db.String)
    code_system_owner_organisation_id = db.Column(db.Integer)
    code_system_owner_organisation_name = db.Column(db.String)

    def __repr__(self):
        return '<Dialect: {} ({}) for Code System: {}>'.format(self.dialect_name, self.dialect_id, self.code_system_name)





# table for all terms (descriptions)
class Terms(db.Model):
    __tablename__ = 'term'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    term_id = db.Column(db.Integer, primary_key=True)
    term_text = db.Column(db.String)
    insert_ts = db.Column(db.DateTime, server_default=func.now())
    update_ts = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Term: {} ({})>'.format(self.term_text, self.term_id)






# table for all codes to be linked to descriptions
class Codes(db.Model):
    __tablename__ = 'code'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    code_id = db.Column(db.Integer, primary_key=True)
    code_text = db.Column(db.String)
    insert_ts = db.Column(db.DateTime, server_default=func.now())
    update_ts = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Code: {} ({})>'.format(self.code_text, self.code_id)






# table for linked organisations, terms and codes ('concepts')
class Concepts(db.Model):
    __tablename__ = 'concept'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    concept_id = db.Column(db.Integer, primary_key=True)
    code_id = db.Column(db.Integer)
    term_id = db.Column(db.Integer)
    organisation_id = db.Column(db.Integer)
    dialect_id = db.Column(db.Integer)
    insert_ts = db.Column(db.DateTime, server_default=func.now())
    update_ts = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Concept: {} from Code: {} and Term: {} in Organisation: {}>'.format(self.concept_id, self.code_id, self.term_id, self.organisation_id)






# suplementary concept information
class ConceptMetadata(db.Model):
    __tablename__ = 'concept_metadata'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    concept_metadata_id = db.Column(db.Integer, primary_key=True)
    concept_id = db.Column(db.Integer)
    obs_number = db.Column(db.Integer)
    first_obs_date = db.Column(db.DateTime)
    last_obs_date = db.Column(db.DateTime)
    insert_ts = db.Column(db.DateTime, server_default=func.now())
    update_ts = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Metadata: {} for Concept: {}>'.format(self.concept_metadata_id, self.concept_id)






# combined view of concepts
class VConcepts(db.Model):
    __tablename__ = 'v_concept'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    concept_id = db.Column(db.Integer, primary_key=True)
    code_id = db.Column(db.Integer)
    code_text = db.Column(db.String)
    term_id = db.Column(db.Integer)
    term_text = db.Column(db.String)
    organisation_id = db.Column(db.Integer, primary_key=True)
    organisation_name = db.Column(db.String)
    dialect_id = db.Column(db.Integer, primary_key=True)
    dialect_name = db.Column(db.String)
    code_system_id = db.Column(db.Integer, primary_key=True)
    code_system_name = db.Column(db.String)
    code_system_owner_organisation_id = db.Column(db.Integer, primary_key=True)
    code_system_owner_organisation_name = db.Column(db.String)
    concept_metadata_id = db.Column(db.Integer)
    obs_number = db.Column(db.Integer)
    first_obs_date = db.Column(db.DateTime)
    last_obs_date = db.Column(db.DateTime)

    @hybrid_property
    def status(self):
        return object_session(self).scalar(select([func.code_mapper.get_concept_status(self.concept_id, session['user_id'], session['target_dialect_id'])]))

    @status.expression
    def status(self):
        return func.code_mapper.get_concept_status(self.concept_id, session['user_id'], session['target_dialect_id'])

    def __repr__(self):
        return '<All details of Concept: {}>'.format(self.concept_id)






# class for custom db function querying
class default_query:
	def query(retobj):
		sel = "select "\
			+ "'Huomio' as huom, "\
			+ "coalesce(code_text,'') as code_text, "\
			+ "coalesce(term_text,'') as term_text, "\
			+ "coalesce(destination_code_text,'') as destination_code_text, "\
			+ "coalesce(destination_term_text,'') as destination_term_text, "\
			+ "coalesce(obs_number,1) as obs_number, "\
			+ "coalesce(to_char(first_obs_date,'yyyy-mm-dd'),'') as first_obs_date, "\
			+ "coalesce(to_char(last_obs_date,'yyyy-mm-dd'),'') as last_obs_date, "\
			+ "coalesce(mapping_user,'') as mapping_user, "\
			+ "coalesce(mapping_ts,'') as mapping_ts, "\
			+ "coalesce(status,'') as status, "\
			+ "coalesce(source_concept_id,-1) as source_concept_id, "\
			+ "coalesce(user_concept_note,'') as user_concept_note"
		fro = " from code_mapper.get_concept_statuses(" + str(session['user_id']) + "," + str(session['source_dialect_id']) + "," + str(session['target_dialect_id']) + ")"
		if retobj == 'select':
			return(sel)
		elif retobj == 'from':
			return(fro)
		else:
			return('something went wrong')






# personal comments for concepts
class Comments(db.Model):
    __tablename__ = 'user_concept_note'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    # define columns properties
    user_id = db.Column(db.Integer, primary_key=True)
    concept_id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String)
    insert_ts = db.Column(db.DateTime, server_default=func.now())
    update_ts = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Comment for Concept: {}>'.format(self.concept_id)






# concept mapping
class Mapping(db.Model):
    __tablename__ = 'mapping'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    # define columns properties
    mapping_id = db.Column(db.Integer, primary_key=True)
    valid = db.Column(db.Boolean)
    user_id = db.Column(db.Integer)
    session_id = db.Column(db.Integer)
    source_concept_id = db.Column(db.Integer)
    destination_concept_id = db.Column(db.Integer)
    event_id = db.Column(db.Integer)
    insert_ts = db.Column(db.DateTime, server_default=func.now())
    update_ts = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Mapping: {} by User: {} from Concept: {} to Concept: {} ({})>'.format(self.mapping_id, self.user_id, self.source_concept_id, self.destination_concept_id, self.mapping_status_id)






# concept mapping
class VMapping(db.Model):
    __tablename__ = 'v_mapping'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    # define columns properties
    mapping_id = db.Column(db.Integer, primary_key=True)
    valid = db.Column(db.Boolean)
    user_id = db.Column(db.Integer)
    username = db.Column(db.String)
    last_name = db.Column(db.String(60))
    first_name = db.Column(db.String(60))
    organisation_id = db.Column(db.Integer)
    organisation_name = db.Column(db.String)
    session_id = db.Column(db.Integer)
    source_concept_id = db.Column(db.Integer)
    source_code_id = db.Column(db.Integer)
    source_code_text = db.Column(db.String)
    source_term_id = db.Column(db.Integer)
    source_term_text = db.Column(db.String)
    source_organisation_id = db.Column(db.Integer)
    source_organisation_name = db.Column(db.String)
    source_dialect_id = db.Column(db.Integer)
    source_dialect_name = db.Column(db.String)
    source_code_system_id = db.Column(db.Integer)
    source_code_system_name = db.Column(db.String)
    source_code_system_owner_organisation_id = db.Column(db.Integer)
    source_code_system_owner_organisation_name = db.Column(db.String)
    source_concept_metadata_id = db.Column(db.Integer)
    source_obs_number = db.Column(db.Integer)
    source_first_obs_date = db.Column(db.DateTime)
    source_last_obs_date = db.Column(db.DateTime)
    destination_concept_id = db.Column(db.Integer)
    destination_code_id = db.Column(db.Integer)
    destination_code_text = db.Column(db.String)
    destination_term_id = db.Column(db.Integer)
    destination_term_text = db.Column(db.String)
    destination_organisation_id = db.Column(db.Integer)
    destination_organisation_name = db.Column(db.String)
    destination_dialect_id = db.Column(db.Integer)
    destination_dialect_name = db.Column(db.String)
    destination_code_system_id = db.Column(db.Integer)
    destination_code_system_name = db.Column(db.String)
    destination_code_system_owner_organisation_id = db.Column(db.Integer)
    destination_code_system_owner_organisation_name = db.Column(db.String)
    destination_concept_metadata_id = db.Column(db.Integer)
    destination_obs_number = db.Column(db.Integer)
    destination_first_obs_date = db.Column(db.DateTime)
    destination_last_obs_date = db.Column(db.DateTime)
    event_type_name = db.Column(db.String)
    comment = db.Column(db.String)
    insert_ts = db.Column(db.DateTime, server_default=func.now())
    update_ts = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<All details of Mapping: {}>'.format(self.mapping_id)






# logging changes
class Event(db.Model):
    __tablename__ = 'event'
    __table_args__ = { 'schema': martti, 'extend_existing': True }

    # define columns properties
    event_id = db.Column(db.Integer, primary_key=True)
    old_mapping_id = db.Column(db.Integer)
    new_mapping_id = db.Column(db.Integer)
    explanation = db.Column(db.String)
    insert_ts = db.Column(db.DateTime, server_default=func.now())
    update_ts = db.Column(db.DateTime, onupdate=func.now())

    def __repr__(self):
        return '<Event: {} ({}) from Mapping: {} to Mapping: {}>'.format(self.explanation, self.event_id, self.old_mapping_id, self.new_mapping_id)
