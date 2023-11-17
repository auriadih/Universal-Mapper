/*#########################
INSERT_CODE
if not exists
*/
DROP FUNCTION IF EXISTS code_mapper.insert_code_if_not_exists(text);
CREATE OR REPLACE FUNCTION code_mapper.insert_code_if_not_exists(_code_text text)
  RETURNS bigint AS $BODY$

DECLARE
_code_id bigint;

BEGIN
	-- get id for given code if it exists
	_code_id := (select code_id from code_mapper.code where code_text = _code_text);

	-- if it doesn't exist, insert it
	if (_code_id is null) then
		insert into code_mapper.code (code_text) values (_code_text) returning code_id into _code_id;

	end if;
	return _code_id;


END;

$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;


/*#########################
INSERT_TERM
if not exists
*/
DROP FUNCTION IF EXISTS code_mapper.insert_term_if_not_exists(text);
CREATE OR REPLACE FUNCTION code_mapper.insert_term_if_not_exists(_term_text text)
  RETURNS bigint AS $BODY$

DECLARE
_term_id bigint;

BEGIN
	-- get id for given term if it exists
	_term_id := (select term_id from code_mapper.term where term_text = _term_text);

	-- if it doesn't exist, insert it
	if (_term_id is null) then
		insert into code_mapper.term (term_text) values (_term_text) returning term_id into _term_id;

	end if;
	return _term_id;


END;

$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;




/*#############################
INSERT_CONCEPT
if not exists
*/
-- Function: code_mapper.insert_concept_if_not_exists(text, text, bigint, bigint)

DROP FUNCTION IF EXISTS code_mapper.insert_concept_if_not_exists(text, text, bigint, bigint);

CREATE OR REPLACE FUNCTION code_mapper.insert_concept_if_not_exists(
    _code_text text,
    _term_text text,
    _organisation_id bigint,
    _dialect_id bigint)
  RETURNS bigint AS
$BODY$

DECLARE
_code_id bigint;
_term_id bigint;
_concept_id bigint;


BEGIN

	_code_id := (select code_mapper.insert_code_if_not_exists(_code_text));
	_term_id := (select code_mapper.insert_term_if_not_exists(_term_text));

	_concept_id := (select concept_id from code_mapper.concept
					where organisation_id = _organisation_id
					and dialect_id = _dialect_id
					and code_id =_code_id
					and term_id = _term_id);

	if (_concept_id is null) then
		insert into code_mapper.concept (code_id, term_id, organisation_id, dialect_id) values
			(_code_id, _term_id, _organisation_id, _dialect_id) returning concept_id into _concept_id;

	end if;
	return _concept_id;

END;

$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;



/* #################
INSERT_MAPPING
*/

-- Function: code_mapper.insert_mapping(bigint, bigint, text, bigint, bigint, bigint, text)

DROP FUNCTION IF EXISTS code_mapper.insert_mapping(bigint, bigint, text, bigint, bigint, bigint, text);

CREATE OR REPLACE FUNCTION code_mapper.insert_mapping(
    _user_id bigint,
    _session_id bigint,
    _event_type_name text,
    _source_concept_id bigint,
    _destination_concept_id bigint DEFAULT NULL::bigint,
    _destination_dialect_id bigint DEFAULT NULL::bigint,
    _comment text DEFAULT NULL::text)
  RETURNS bigint AS
$BODY$

DECLARE
_event_type_id bigint;
_mapping_id bigint;
_old_mapping RECORD;


BEGIN


	_event_type_id := (select event_type_id from code_mapper.event_type where name = _event_type_name);

	-- a mapping may already exist for this source concept

	-- if a destination dialect was given
	if (_destination_dialect_id is not null) then
		execute format('select m.mapping_id, e.name as event_type_name
				from code_mapper.mapping as m
				inner join code_mapper.event_type as e on m.event_type_id = e.event_type_id
				where source_concept_id = %1$s
				and (destination_dialect_id = %2$s or destination_dialect_id is null)
				and valid = true', _source_concept_id, _destination_dialect_id) into _old_mapping;

	-- if a destination dialect was not given, i.e. the source concept was determined to be incorrect
	else
		execute format('select m.mapping_id, e.name as event_type_name
				from code_mapper.mapping as m
				inner join code_mapper.event_type as e on m.event_type_id = e.event_type_id
				where source_concept_id = %1$s
				and valid = true', _source_concept_id) into _old_mapping;

	end if;
	
	
	
	-- if an old mapping for the same term to the same destination dialect exists
	if (_old_mapping.mapping_id is not null) then

		-- if current mapping is a bridge mapping, it should not replace older user-made mapping
		if (_event_type_name = 'Bridge mapping' and _old_mapping.event_type_name != 'Bridge mapping') then
			insert into code_mapper.mapping (user_id, session_id, source_concept_id, destination_concept_id, destination_dialect_id, event_type_id, comment, valid) values 
				(_user_id, _session_id, _source_concept_id, _destination_concept_id, _destination_dialect_id, _event_type_id, _comment, false) returning mapping_id into _mapping_id;

		-- if current is user-made, it should replace any older mapping for the same term
		else
			insert into code_mapper.mapping (user_id, session_id, source_concept_id, destination_concept_id, destination_dialect_id, event_type_id, comment, valid) values 
				(_user_id, _session_id, _source_concept_id, _destination_concept_id, _destination_dialect_id, _event_type_id, _comment, true) returning mapping_id into _mapping_id;
			update code_mapper.mapping set valid = false where mapping_id = _old_mapping.mapping_id; -- replace old mapping with new user-made mapping
		end if;

	-- if no mapping exists yet for this source concept
	else 
		insert into code_mapper.mapping (user_id, session_id, source_concept_id, destination_concept_id, destination_dialect_id, event_type_id, comment, valid) values 
				(_user_id, _session_id, _source_concept_id, _destination_concept_id, _destination_dialect_id, _event_type_id, _comment, true) returning mapping_id into _mapping_id;
	
	end if;

	return _mapping_id;

END;

$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

  
