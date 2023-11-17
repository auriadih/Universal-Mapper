

-- Snomed II terms from PSHP

-- T_SNOMED
drop materialized view if exists snomed.mv_tays_t_snomed;
create materialized view snomed.mv_tays_t_snomed as
select
    coalesce(btrim(e.transformtext), '') as t_snomed_original,
    coalesce(btrim(e.u_text), '') as elin,
    count_in_2014 + count_in_2015 + count_in_2016 + count_in_2017 as naytenumero_count,
    substring(btrim(e.transformtext), 1, 6) as t_snomed_harmonized
   FROM snomed.tays_snomed2 e
  WHERE transformtext ~* '^T';

  



-- M_SNOMED
drop materialized view if exists snomed.mv_tays_m_snomed;
create materialized view snomed.mv_tays_m_snomed as
select
    coalesce(btrim(e.transformtext), '') as m_snomed_original,
    coalesce(btrim(e.u_text), '') as diagnoosi,
    count_in_2014 + count_in_2015 + count_in_2016 + count_in_2017 as naytenumero_count,
    substring(btrim(e.transformtext), 1, 6) as m_snomed_harmonized
   FROM snomed.tays_snomed2 e
  WHERE transformtext !~* '^T';

 

-- truncate table code_mapper.term cascade;
-- truncate table code_mapper.code cascade;
-- select setval('code_mapper.code__seq'::regclass, 1);
-- select setval('code_mapper.term__seq'::regclass, 1);
-- truncate table code_mapper.synonym cascade;
-- select setval('code_mapper.synonym__seq'::regclass, 1);
-- truncate table code_mapper.concept cascade;
-- select setval('code_mapper.concept__seq'::regclass, 1);
-- truncate table code_mapper.concept_metadata;
-- select setval('code_mapper.concept_metadata__seq'::regclass, 1);


-- terms
insert into code_mapper.term (term_text)
select distinct elin
from snomed.mv_tays_t_snomed on conflict do nothing;

insert into code_mapper.term (term_text)
select distinct diagnoosi
from snomed.mv_tays_m_snomed on conflict do nothing;


-- codes
insert into code_mapper.code (code_text)
select distinct t_snomed_harmonized
from snomed.mv_tays_t_snomed  on conflict do nothing;

insert into code_mapper.code (code_text)
select distinct m_snomed_harmonized
from snomed.mv_tays_m_snomed  on conflict do nothing;


-- synonyms
insert into code_mapper.synonym (synonym, code_id, dialect_id)
select distinct t_snomed_original,
	c.code_id,
		(select dialect_id from code_mapper.dialect as d
		inner join code_mapper.code_system as c on d.code_system_id = c.code_system_id
		where d.dialect_name = 'PSHP dialect' and c.name = 'Snomed II')
from snomed.mv_tays_t_snomed as s
inner join code_mapper.code as c on s.t_snomed_harmonized = c.code_text
where t_snomed_original != t_snomed_harmonized;


insert into code_mapper.synonym (synonym, code_id, dialect_id)
select distinct m_snomed_original,
		c.code_id,
		(select dialect_id from code_mapper.dialect as d
			inner join code_mapper.code_system as c on d.code_system_id = c.code_system_id
			where d.dialect_name = 'PSHP dialect' and c.name = 'Snomed II')
from snomed.mv_tays_m_snomed as s
inner join code_mapper.code as c on s.m_snomed_harmonized = c.code_text
where s.m_snomed_original != s.m_snomed_harmonized;




-- concepts
with concepts as (
select distinct t_snomed_harmonized as code, elin as term
from snomed.mv_tays_t_snomed
union
select distinct m_snomed_harmonized as code, diagnoosi as term
from snomed.mv_tays_m_snomed
)

select code_mapper.insert_concept_if_not_exists(_code_text := s.code, _term_text := s.term, _organisation_id := o.organisation_id, _dialect_id := d.dialect_id)
from concepts as s
inner join code_mapper.organisation  as o on o.name = 'PSHP'
inner join code_mapper.dialect as d on d.dialect_name = 'PSHP dialect'
inner join code_mapper.code_system as c on d.code_system_id = c.code_system_id and c.name = 'Snomed II';



-- concept_metadata
insert into code_mapper.concept_metadata (concept_id, obs_number)
select co.concept_id, s.naytenumero_count
from snomed.mv_tays_t_snomed as s
inner join code_mapper.code as c on s.t_snomed_harmonized = c.code_text
inner join code_mapper.term as t on s.elin = t.term_text
inner join code_mapper.concept as co on c.code_id = co.code_id and co.term_id = t.term_id
inner join code_mapper.organisation as o on co.organisation_id = o.organisation_id and o.name = 'PSHP'
inner join code_mapper.dialect as d on co.dialect_id = d.dialect_id and d.dialect_name = 'PSHP dialect';


insert into code_mapper.concept_metadata (concept_id, obs_number)
select co.concept_id, s.naytenumero_count
from snomed.mv_tays_m_snomed as s
inner join code_mapper.code as c on s.m_snomed_harmonized = c.code_text
inner join code_mapper.term as t on s.diagnoosi = t.term_text
inner join code_mapper.concept as co on c.code_id = co.code_id and co.term_id = t.term_id
inner join code_mapper.organisation as o on co.organisation_id = o.organisation_id and o.name = 'PSHP'
inner join code_mapper.dialect as d on co.dialect_id = d.dialect_id and d.dialect_name = 'PSHP dialect';








