-- DROP VIEW snomed.v_snomed2_bridge;

CREATE OR REPLACE VIEW snomed.v_snomed2_bridge AS 
 SELECT btrim(replace(snomed2_bridge.code2::text, '-'::text, ''::text)) AS code2_harmonized,
	btrim(snomed2_bridge.code2) as code2_original,
    snomed2_bridge.nomen2,
    snomed2_bridge.class2,
    snomed2_bridge.conceptid,
    snomed2_bridge.snomedid,
    snomed2_bridge.descriptionid,
    snomed2_bridge.term,
    snomed2_bridge.type,
    snomed2_bridge.additional_code
   FROM snomed.snomed2_bridge;




-- select * from snomed.v_snomed2_bridge
-- limit 100;


-- #####################

-- Snomed II terms
-- 42 060
insert into code_mapper.term (term_text)
select distinct nomen2
from snomed.v_snomed2_bridge on conflict do nothing;


-- Snomed II codes
-- 27 676
insert into code_mapper.code (code_text)
select distinct code2_harmonized
from snomed.v_snomed2_bridge  on conflict do nothing;


-- Snomed II synonyms
-- 30 526
insert into code_mapper.synonym (synonym, code_id, dialect_id)
select distinct code2_original,
	c.code_id,
		(select dialect_id from code_mapper.dialect as d
		inner join code_mapper.code_system as c on d.code_system_id = c.code_system_id
		where d.dialect_name = 'Official bridge to Snomed CT' and c.name = 'Snomed II')
from snomed.v_snomed2_bridge as s
inner join code_mapper.code as c on s.code2_harmonized = c.code_text
where code2_original != code2_harmonized;

-- Snomed II concepts
-- 42 120
with concepts as (
select distinct code2_harmonized as code, nomen2 as term
from snomed.v_snomed2_bridge 
)

select code_mapper.insert_concept_if_not_exists(_code_text := s.code, _term_text := s.term, _organisation_id := o.organisation_id, _dialect_id := d.dialect_id)
from concepts as s
inner join code_mapper.organisation  as o on o.name = 'IHTSDO'
inner join code_mapper.dialect as d on d.dialect_name = 'Official bridge to Snomed CT'
inner join code_mapper.code_system as c on d.code_system_id = c.code_system_id and c.name = 'Snomed II';





-- #####################


-- Snomed CT terms
-- 19 458
insert into code_mapper.term (term_text)
select distinct term
from snomed.v_snomed2_bridge
where term is not null
on conflict do nothing;


-- Snomed CT codes
-- 32 468
insert into code_mapper.code (code_text)
select distinct conceptid
from snomed.v_snomed2_bridge
where conceptid is not null 
on conflict do nothing;


-- Snomed CT concepts
-- 38 951
with concepts as (
select distinct conceptid::text as code, term
from snomed.v_snomed2_bridge
where term is not null and conceptid is not null
)

select code_mapper.insert_concept_if_not_exists(_code_text := s.code, _term_text := s.term, _organisation_id := o.organisation_id, _dialect_id := d.dialect_id)
from concepts as s
inner join code_mapper.organisation  as o on o.name = 'IHTSDO'
inner join code_mapper.dialect as d on d.dialect_name = 'International Snomed CT'
inner join code_mapper.code_system as c on d.code_system_id = c.code_system_id and c.name = 'Snomed CT';


-- ############################

-- mappings



with snomed2 as
(select concept_id, code_text, term_text from code_mapper.v_concept
where code_system_name = 'Snomed II' and dialect_name = 'Official bridge to Snomed CT' and organisation_name = 'IHTSDO'),

snomedct as
(select concept_id, code_text, term_text from code_mapper.v_concept
where code_system_name = 'Snomed CT' and dialect_name = 'International Snomed CT' and organisation_name = 'IHTSDO')

select code_mapper.insert_mapping( _user_id := u.user_id,
    _session_id := -101::bigint,
    _event_type_name := 'Bridge mapping'::text,
    _source_concept_id := snomed2.concept_id,
    _destination_concept_id := snomedct.concept_id
    -- , _destination_dialect_id := null::bigint, _comment := null::text
    )

from snomed2
inner join snomed.v_snomed2_bridge as b on b.code2_harmonized = snomed2.code_text and b.nomen2 = snomed2.term_text
inner join snomedct on b.conceptid::text = snomedct.code_text and b.term = snomedct.term_text
inner join code_mapper.user as u on u.last_name = 'Dummy'
where b.type = 'Match';


