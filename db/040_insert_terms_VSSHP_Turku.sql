

-- Snomed II terms from VSSHP

-- T_SNOMED
drop materialized view snomed.mv_vsshp_t_snomed;
create materialized view snomed.mv_vsshp_t_snomed as
select
    coalesce(btrim(e.t_snomed), '') as t_snomed_original,
    coalesce(btrim(e.elin), '') as elin,
    min(e.naytteenottohetki) as min_ts,
    max(naytteenottohetki) as max_ts,
    count(distinct naytenumero) as naytenumero_count,
    
        CASE
            WHEN length(btrim(e.t_snomed)::text) = 8 AND btrim(e.t_snomed)::text ~* 'T....0[12].'::text THEN "overlay"(btrim(e.t_snomed)::text, ''::text, 6, 2)::character varying
            ELSE coalesce(btrim(e.t_snomed), '')
        END AS t_snomed_harmonized
   FROM main.patologia_elin_diagnoosi e
  WHERE e.naytenumero::text ~* '^[ABCDNRSYK][^N]'::text
  and t_snomed !~* '^M'
  group by t_snomed, elin;

-- M_SNOMED
drop materialized view snomed.mv_vsshp_m_snomed;
create materialized view snomed.mv_vsshp_m_snomed as
select
    coalesce(btrim(e.m_snomed), '') as m_snomed_original,
    coalesce(btrim(e.diagnoosi), '') as diagnoosi,
    min(e.naytteenottohetki) as min_ts,
    max(naytteenottohetki) as max_ts,
    count(distinct naytenumero) as naytenumero_count,
    
        CASE
            WHEN length(btrim(e.m_snomed)::text) = 8 AND btrim(e.m_snomed)::text ~* 'M....0[1234].'::text THEN "overlay"(btrim(e.m_snomed)::text, ''::text, 6, 2)::character varying
            ELSE coalesce(btrim(e.m_snomed), '')
        END AS m_snomed_harmonized
   FROM main.patologia_elin_diagnoosi e
  WHERE e.naytenumero::text ~* '^[ABCDNRSYK][^N]'::text
  and m_snomed !~* '^T'
  group by m_snomed, diagnoosi;
  


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
from snomed.mv_vsshp_t_snomed on conflict do nothing;

insert into code_mapper.term (term_text)
select distinct diagnoosi
from snomed.mv_vsshp_m_snomed on conflict do nothing;


-- codes
insert into code_mapper.code (code_text)
select distinct t_snomed_harmonized
from snomed.mv_vsshp_t_snomed  on conflict do nothing;

insert into code_mapper.code (code_text)
select distinct m_snomed_harmonized
from snomed.mv_vsshp_m_snomed  on conflict do nothing;


-- synonyms
insert into code_mapper.synonym (synonym, code_id, dialect_id)
select distinct t_snomed_original,
	c.code_id,
		(select dialect_id from code_mapper.dialect as d
		inner join code_mapper.code_system as c on d.code_system_id = c.code_system_id
		where d.dialect_name = 'VSSHP dialect' and c.name = 'Snomed II')
from snomed.mv_vsshp_t_snomed as s
inner join code_mapper.code as c on s.t_snomed_harmonized = c.code_text
where t_snomed_original != t_snomed_harmonized;


insert into code_mapper.synonym (synonym, code_id, dialect_id)
select distinct m_snomed_original,
		c.code_id,
		(select dialect_id from code_mapper.dialect as d
			inner join code_mapper.code_system as c on d.code_system_id = c.code_system_id
			where d.dialect_name = 'VSSHP dialect' and c.name = 'Snomed II')
from snomed.mv_vsshp_m_snomed as s
inner join code_mapper.code as c on s.m_snomed_harmonized = c.code_text
where s.m_snomed_original != s.m_snomed_harmonized;




-- concepts
with concepts as (
select distinct t_snomed_harmonized as code, elin as term
from snomed.mv_vsshp_t_snomed
union
select distinct m_snomed_harmonized as code, diagnoosi as term
from snomed.mv_vsshp_m_snomed
)

select code_mapper.insert_concept_if_not_exists(_code_text := s.code, _term_text := s.term, _organisation_id := o.organisation_id, _dialect_id := d.dialect_id)
from concepts as s
inner join code_mapper.organisation  as o on o.name = 'VSSHP'
inner join code_mapper.dialect as d on d.dialect_name = 'VSSHP dialect'
inner join code_mapper.code_system as c on d.code_system_id = c.code_system_id and c.name = 'Snomed II';



-- concept_metadata
insert into code_mapper.concept_metadata (concept_id, obs_number, first_obs_date, last_obs_date)
select co.concept_id, s.naytenumero_count, min_ts::date, max_ts::date
from snomed.mv_vsshp_t_snomed as s
inner join code_mapper.code as c on s.t_snomed_harmonized = c.code_text
inner join code_mapper.term as t on s.elin = t.term_text
inner join code_mapper.concept as co on c.code_id = co.code_id and co.term_id = t.term_id
inner join code_mapper.organisation as o on co.organisation_id = o.organisation_id and o.name = 'VSSHP'
inner join code_mapper.dialect as d on co.dialect_id = d.dialect_id and d.dialect_name = 'VSSHP dialect';


insert into code_mapper.concept_metadata (concept_id, obs_number, first_obs_date, last_obs_date)
select co.concept_id, s.naytenumero_count, min_ts::date, max_ts::date
from snomed.mv_vsshp_m_snomed as s
inner join code_mapper.code as c on s.m_snomed_harmonized = c.code_text
inner join code_mapper.term as t on s.diagnoosi = t.term_text
inner join code_mapper.concept as co on c.code_id = co.code_id and co.term_id = t.term_id
inner join code_mapper.organisation as o on co.organisation_id = o.organisation_id and o.name = 'VSSHP'
inner join code_mapper.dialect as d on co.dialect_id = d.dialect_id and d.dialect_name = 'VSSHP dialect';









