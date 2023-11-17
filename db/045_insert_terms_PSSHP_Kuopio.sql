

-- Snomed II terms from kys

-- T_SNOMED
drop materialized view if exists snomed.mv_kys_t_snomed;

create materialized view snomed.mv_kys_t_snomed as
with cte as (
select 
t_snomed, elin, min(alkuhetki) as alkuhetki, max(loppuhetki) as loppuhetki, sum(lkm) as lkm
from snomed.kys_snomed2_elimet
group by t_snomed, elin)

select 
t_snomed as t_snomed_original,
elin,
lkm as naytenumero_count,
t_snomed as t_snomed_harmonized,
alkuhetki as min_ts,
loppuhetki as max_ts

from cte;


-- M_SNOMED
drop materialized view if exists snomed.mv_kys_m_snomed;

create materialized view snomed.mv_kys_m_snomed as
with cte as (
select 
m_snomed, diagnoosi, min(alkuhetki) as alkuhetki, max(loppuhetki) as loppuhetki, sum(lkm) as lkm
from snomed.kys_snomed2_diagnoosit
group by m_snomed, diagnoosi)

select 
m_snomed as m_snomed_original,
diagnoosi,
lkm as naytenumero_count,
m_snomed as m_snomed_harmonized,
alkuhetki as min_ts,
loppuhetki as max_ts

from cte;


-- terms
insert into code_mapper.term (term_text)
select distinct elin
from snomed.mv_kys_t_snomed on conflict do nothing;

insert into code_mapper.term (term_text)
select distinct diagnoosi
from snomed.mv_kys_m_snomed on conflict do nothing;


-- codes
insert into code_mapper.code (code_text)
select distinct t_snomed_harmonized
from snomed.mv_kys_t_snomed  on conflict do nothing;

insert into code_mapper.code (code_text)
select distinct m_snomed_harmonized
from snomed.mv_kys_m_snomed  on conflict do nothing;


-- synonyms
insert into code_mapper.synonym (synonym, code_id, dialect_id)
select distinct t_snomed_original,
	c.code_id,
		(select dialect_id from code_mapper.dialect as d
		inner join code_mapper.code_system as c on d.code_system_id = c.code_system_id
		where d.dialect_name = 'PSSHP dialect' and c.name = 'Snomed II')
from snomed.mv_kys_t_snomed as s
inner join code_mapper.code as c on s.t_snomed_harmonized = c.code_text
where t_snomed_original != t_snomed_harmonized;


insert into code_mapper.synonym (synonym, code_id, dialect_id)
select distinct m_snomed_original,
		c.code_id,
		(select dialect_id from code_mapper.dialect as d
			inner join code_mapper.code_system as c on d.code_system_id = c.code_system_id
			where d.dialect_name = 'PSSHP dialect' and c.name = 'Snomed II')
from snomed.mv_kys_m_snomed as s
inner join code_mapper.code as c on s.m_snomed_harmonized = c.code_text
where s.m_snomed_original != s.m_snomed_harmonized;


-- delete from code_mapper.term where term_text LIKE 'T????? %';
-- delete from code_mapper.term where term_text LIKE 'M????? %';


-- concepts
with concepts as (
select distinct t_snomed_harmonized as code, elin as term
from snomed.mv_kys_t_snomed
union
select distinct m_snomed_harmonized as code, diagnoosi as term
from snomed.mv_kys_m_snomed
)

select code_mapper.insert_concept_if_not_exists(_code_text := s.code, _term_text := s.term, _organisation_id := o.organisation_id, _dialect_id := d.dialect_id)
from concepts as s
inner join code_mapper.organisation  as o on o.name = 'PSSHP'
inner join code_mapper.dialect as d on d.dialect_name = 'PSSHP dialect'
inner join code_mapper.code_system as c on d.code_system_id = c.code_system_id and c.name = 'Snomed II';


-- concept_metadata
insert into code_mapper.concept_metadata (concept_id, obs_number)
select co.concept_id, s.naytenumero_count
from snomed.mv_kys_t_snomed as s
inner join code_mapper.code as c on s.t_snomed_harmonized = c.code_text
inner join code_mapper.term as t on s.elin = t.term_text
inner join code_mapper.concept as co on c.code_id = co.code_id and co.term_id = t.term_id
inner join code_mapper.organisation as o on co.organisation_id = o.organisation_id and o.name = 'PSSHP'
inner join code_mapper.dialect as d on co.dialect_id = d.dialect_id and d.dialect_name = 'PSSHP dialect';


insert into code_mapper.concept_metadata (concept_id, obs_number)
select co.concept_id, s.naytenumero_count
from snomed.mv_kys_m_snomed as s
inner join code_mapper.code as c on s.m_snomed_harmonized = c.code_text
inner join code_mapper.term as t on s.diagnoosi = t.term_text
inner join code_mapper.concept as co on c.code_id = co.code_id and co.term_id = t.term_id
inner join code_mapper.organisation as o on co.organisation_id = o.organisation_id and o.name = 'PSSHP'
inner join code_mapper.dialect as d on co.dialect_id = d.dialect_id and d.dialect_name = 'PSSHP dialect';











