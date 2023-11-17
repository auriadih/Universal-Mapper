DO $$

DECLARE

_ihtsdo_id bigint;
_snomed2_id bigint;
_snomedct_id bigint;

BEGIN

-- insert organisations
INSERT INTO code_mapper.organisation(name, city, country) VALUES
('VSSHP', 'Turku', 'Finland'),
('THL', 'Helsinki', 'Finland'),
('IHTSDO', 'World', 'World'),
('PSHP', 'Tampere', 'Finland'),
('PPSHP', 'Oulu', 'Finland'),
('HUS', 'Helsinki', 'Finland'),
('KSSHP', 'Jyväskylä', 'Finland'),
('PSSHP', 'Kuopio', 'Finland');

_ihtsdo_id := (select organisation_id from code_mapper.organisation where name = 'IHTSDO');

-- insert code systems
INSERT INTO code_mapper.code_system(name, owner_organisation_id) VALUES
('Snomed II', _ihtsdo_id) returning code_system_id into _snomed2_id;

INSERT INTO code_mapper.code_system(name, owner_organisation_id) VALUES
('Snomed CT', _ihtsdo_id) returning code_system_id into _snomedct_id;


-- insert dialects

INSERT INTO code_mapper.dialect(code_system_id, dialect_name, is_official) VALUES
(_snomed2_id, 'VSSHP dialect', false),
(_snomedct_id, 'International Snomed CT', true),
(_snomed2_id, 'Official bridge to Snomed CT', true),
(_snomed2_id, 'PSHP dialect', false),
(_snomed2_id, 'PPSHP dialect', false),
(_snomed2_id, 'HUS dialect', false),
(_snomed2_id, 'KSSHP dialect', false),
(_snomed2_id, 'PSSHP dialect', false);


-- insert event_types
insert into code_mapper.event_type (name) values
('Incorrect concept'),
('No match for concept in target dialect'),
('Bridge mapping'),
('User mapping');


END $$;

-- #############################
-- insert users

DO $$

DECLARE

_vsshp_id bigint:= (select organisation_id from code_mapper.organisation where name = 'VSSHP');
_pshp_id bigint:= (select organisation_id from code_mapper.organisation where name = 'PSHP');
_ppshp_id bigint:= (select organisation_id from code_mapper.organisation where name = 'PPSHP');
_psshp_id bigint:= (select organisation_id from code_mapper.organisation where name = 'PSSHP');
_ksshp_id bigint:= (select organisation_id from code_mapper.organisation where name = 'KSSHP');
_hus_id bigint:= (select organisation_id from code_mapper.organisation where name = 'HUS');
_thl_id bigint:= (select organisation_id from code_mapper.organisation where name = 'THL');


_snomed_ct_id bigint;
_vsshp_d_id bigint;
_ppshp_d_id bigint;
_pshp_d_id bigint;
_psshp_d_id bigint;
_ksshp_d_id bigint;
_hus_d_id bigint;
_thl_d_id bigint;


BEGIN

_snomed_ct_id := (select dialect_id
										from code_mapper.dialect as d
										inner join code_mapper.code_system as cs on d.code_system_id = cs.code_system_id
										where cs.name = 'Snomed CT'
										and d.dialect_name = 'International Snomed CT');

										
_vsshp_d_id := (select dialect_id
										from code_mapper.dialect as d
										inner join code_mapper.code_system as cs on d.code_system_id = cs.code_system_id
										where cs.name = 'Snomed II'
										and d.dialect_name = 'VSSHP dialect');
										
_ppshp_d_id := (select dialect_id
										from code_mapper.dialect as d
										inner join code_mapper.code_system as cs on d.code_system_id = cs.code_system_id
										where cs.name = 'Snomed II'
										and d.dialect_name = 'PPSHP dialect');
										
_pshp_d_id := (select dialect_id
										from code_mapper.dialect as d
										inner join code_mapper.code_system as cs on d.code_system_id = cs.code_system_id
										where cs.name = 'Snomed II'
										and d.dialect_name = 'PSHP dialect');
										
_psshp_d_id := (select dialect_id
										from code_mapper.dialect as d
										inner join code_mapper.code_system as cs on d.code_system_id = cs.code_system_id
										where cs.name = 'Snomed II'
										and d.dialect_name = 'PSSHP dialect');
										
_hus_d_id := (select dialect_id
										from code_mapper.dialect as d
										inner join code_mapper.code_system as cs on d.code_system_id = cs.code_system_id
										where cs.name = 'Snomed II'
										and d.dialect_name = 'HUS dialect');

-- insert users
insert into code_mapper.user (first_name, last_name, username, email, organisation_id, password_hash,
insert_ts, default_source_dialect_id, default_destination_dialect_id)
values

...

;

-- insert dummy session
insert into code_mapper.session (session_id, user_id, start_ts, end_ts) values
(-101, (select user_id from code_mapper.user where last_name = 'Dummy'),
now(), now() + interval '100 year');


END $$;


