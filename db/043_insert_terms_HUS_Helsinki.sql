

-- Snomed II terms from HUS

-- T_SNOMED
drop materialized view if exists snomed.mv_hus_t_snomed;
create materialized view snomed.mv_hus_t_snomed as
select
    coalesce(btrim(e.t_snomed), '') as t_snomed_original,
    coalesce(btrim(e.organ), '') as elin,
    n as naytenumero_count,
    coalesce(btrim(e.t_snomed), '') as t_snomed_harmonized
   FROM snomed.hus_snomed2_elimet as e;

  



-- M_SNOMED
drop materialized view if exists snomed.mv_hus_m_snomed;
create materialized view snomed.mv_hus_m_snomed as
select
    coalesce(btrim(e.m_snomed), '') as m_snomed_original,
    coalesce(btrim(e.diagnose), '') as diagnoosi,
    n as naytenumero_count,
    coalesce(btrim(e.m_snomed), '') as m_snomed_harmonized
   FROM snomed.hus_snomed2_diagnoosit as e;



-- terms
insert into code_mapper.term (term_text)
select distinct elin
from snomed.mv_hus_t_snomed on conflict do nothing;

insert into code_mapper.term (term_text)
select distinct diagnoosi
from snomed.mv_hus_m_snomed on conflict do nothing;


-- codes
insert into code_mapper.code (code_text)
select distinct t_snomed_harmonized
from snomed.mv_hus_t_snomed  on conflict do nothing;

insert into code_mapper.code (code_text)
select distinct m_snomed_harmonized
from snomed.mv_hus_m_snomed  on conflict do nothing;


-- synonyms
insert into code_mapper.synonym (synonym, code_id, dialect_id)
select distinct t_snomed_original,
	c.code_id,
		(select dialect_id from code_mapper.dialect as d
		inner join code_mapper.code_system as c on d.code_system_id = c.code_system_id
		where d.dialect_name = 'HUS dialect' and c.name = 'Snomed II')
from snomed.mv_hus_t_snomed as s
inner join code_mapper.code as c on s.t_snomed_harmonized = c.code_text
where t_snomed_original != t_snomed_harmonized;


insert into code_mapper.synonym (synonym, code_id, dialect_id)
select distinct m_snomed_original,
		c.code_id,
		(select dialect_id from code_mapper.dialect as d
			inner join code_mapper.code_system as c on d.code_system_id = c.code_system_id
			where d.dialect_name = 'HUS dialect' and c.name = 'Snomed II')
from snomed.mv_hus_m_snomed as s
inner join code_mapper.code as c on s.m_snomed_harmonized = c.code_text
where s.m_snomed_original != s.m_snomed_harmonized;




-- concepts
with concepts as (
select distinct t_snomed_harmonized as code, elin as term
from snomed.mv_hus_t_snomed
union
select distinct m_snomed_harmonized as code, diagnoosi as term
from snomed.mv_hus_m_snomed
)

select code_mapper.insert_concept_if_not_exists(_code_text := s.code, _term_text := s.term, _organisation_id := o.organisation_id, _dialect_id := d.dialect_id)
from concepts as s
inner join code_mapper.organisation  as o on o.name = 'HUS'
inner join code_mapper.dialect as d on d.dialect_name = 'HUS dialect'
inner join code_mapper.code_system as c on d.code_system_id = c.code_system_id and c.name = 'Snomed II';



-- concept_metadata
insert into code_mapper.concept_metadata (concept_id, obs_number)
select co.concept_id, s.naytenumero_count
from snomed.mv_hus_t_snomed as s
inner join code_mapper.code as c on s.t_snomed_harmonized = c.code_text
inner join code_mapper.term as t on s.elin = t.term_text
inner join code_mapper.concept as co on c.code_id = co.code_id and co.term_id = t.term_id
inner join code_mapper.organisation as o on co.organisation_id = o.organisation_id and o.name = 'HUS'
inner join code_mapper.dialect as d on co.dialect_id = d.dialect_id and d.dialect_name = 'HUS dialect';


insert into code_mapper.concept_metadata (concept_id, obs_number)
select co.concept_id, s.naytenumero_count
from snomed.mv_hus_m_snomed as s
inner join code_mapper.code as c on s.m_snomed_harmonized = c.code_text
inner join code_mapper.term as t on s.diagnoosi = t.term_text
inner join code_mapper.concept as co on c.code_id = co.code_id and co.term_id = t.term_id
inner join code_mapper.organisation as o on co.organisation_id = o.organisation_id and o.name = 'HUS'
inner join code_mapper.dialect as d on co.dialect_id = d.dialect_id and d.dialect_name = 'HUS dialect';








