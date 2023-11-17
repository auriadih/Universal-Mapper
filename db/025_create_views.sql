

DROP VIEW IF EXISTS code_mapper.v_mapping_statistics;
DROP VIEW IF EXISTS code_mapper.v_mapping;
DROP VIEW IF EXISTS code_mapper.v_concept;
DROP VIEW IF EXISTS code_mapper.v_synonym;
DROP VIEW IF EXISTS code_mapper.v_dialect;
DROP VIEW IF EXISTS code_mapper.v_user;




-- View: code_mapper.v_user

CREATE OR REPLACE VIEW code_mapper.v_user AS 
 SELECT u.user_id,
    u.username,
    u.password_hash,
    u.email,
    u.last_name,
    u.first_name,
    o.organisation_id,
    o.name AS organisation_name,
    u.insert_ts,
    u.update_ts
   FROM code_mapper."user" u
     JOIN code_mapper.organisation o ON u.organisation_id = o.organisation_id;



-- View: code_mapper.v_dialect

CREATE OR REPLACE VIEW code_mapper.v_dialect AS 
 SELECT d.dialect_id,
    d.dialect_name,
    d.is_official,
    cs.code_system_id,
    cs.name AS code_system_name,
    o.organisation_id AS code_system_owner_organisation_id,
    o.name AS code_system_owner_organisation_name
   FROM code_mapper.dialect d
     JOIN code_mapper.code_system cs ON d.code_system_id = cs.code_system_id
     JOIN code_mapper.organisation o ON cs.owner_organisation_id = o.organisation_id;


-- View: code_mapper.v_synonym

CREATE OR REPLACE VIEW code_mapper.v_synonym AS
SELECT 
s.code_id, c.code_text, s.synonym_id, s.synonym,
s.dialect_id, d.dialect_name
FROM code_mapper.synonym as s
inner join code_mapper.code as c on s.code_id = c.code_id
inner join code_mapper.dialect as d on s.dialect_id = d.dialect_id
;



-- View: code_mapper.v_concept

CREATE OR REPLACE VIEW code_mapper.v_concept AS 
 SELECT co.concept_id,
    c.code_id,
    c.code_text,
    t.term_id,
    t.term_text,
    o.organisation_id,
    o.name AS organisation_name,
    d.dialect_id,
    d.dialect_name,
    d.is_official,
    cs.code_system_id,
    cs.name AS code_system_name,
    o2.organisation_id AS code_system_owner_organisation_id,
    o2.name AS code_system_owner_organisation_name,
    m.concept_metadata_id,
    m.obs_number,
    m.first_obs_date,
    m.last_obs_date
   FROM code_mapper.concept co
     JOIN code_mapper.code c ON co.code_id = c.code_id
     JOIN code_mapper.term t ON co.term_id = t.term_id
     JOIN code_mapper.organisation o ON co.organisation_id = o.organisation_id
     JOIN code_mapper.dialect d ON co.dialect_id = d.dialect_id
     JOIN code_mapper.code_system cs ON d.code_system_id = cs.code_system_id
     JOIN code_mapper.organisation o2 ON cs.owner_organisation_id = o2.organisation_id
     LEFT JOIN code_mapper.concept_metadata m ON co.concept_id = m.concept_id;




-- View: code_mapper.v_mapping

CREATE OR REPLACE VIEW code_mapper.v_mapping AS 
 SELECT m.mapping_id,
    m.valid,
    u.user_id,
    u.username,
    u.last_name,
    u.first_name,
    u.organisation_id,
    u.organisation_name,
    m.session_id,
    m.source_concept_id,
    source.code_id AS source_code_id,
    source.code_text AS source_code_text,
    source.term_id AS source_term_id,
    source.term_text AS source_term_text,
    source.organisation_id AS source_organisation_id,
    source.organisation_name AS source_organisation_name,
    source.dialect_id AS source_dialect_id,
    source.dialect_name AS source_dialect_name,
    source.code_system_id AS source_code_system_id,
    source.code_system_name AS source_code_system_name,
    source.code_system_owner_organisation_id AS source_code_system_owner_organisation_id,
    source.code_system_owner_organisation_name AS source_code_system_owner_organisation_name,
    source.concept_metadata_id AS source_concept_metadata_id,
    source.obs_number AS source_obs_number,
    source.first_obs_date AS source_first_obs_date,
    source.last_obs_date AS source_last_obs_date,
    m.destination_concept_id,
    destination.code_id AS destination_code_id,
    destination.code_text AS destination_code_text,
    destination.term_id AS destination_term_id,
    destination.term_text AS destination_term_text,
    destination.organisation_id AS destination_organisation_id,
    destination.organisation_name AS destination_organisation_name,
    case when destination.concept_id is not null then destination.dialect_id else dd.dialect_id end AS destination_dialect_id,
    case when destination.concept_id is not null then destination.dialect_name else dd.dialect_name end AS destination_dialect_name,
    destination.code_system_id AS destination_code_system_id,
    destination.code_system_name AS destination_code_system_name,
    destination.code_system_owner_organisation_id AS destination_code_system_owner_organisation_id,
    destination.code_system_owner_organisation_name AS destination_code_system_owner_organisation_name,
    destination.concept_metadata_id AS destination_concept_metadata_id,
    destination.obs_number AS destination_obs_number,
    destination.first_obs_date AS destination_first_obs_date,
    destination.last_obs_date AS destination_last_obs_date,
    et.name as event_type_name,
    m.comment,
    m.insert_ts,
    m.update_ts
   FROM code_mapper.mapping m
     JOIN code_mapper.v_concept source ON m.source_concept_id = source.concept_id
     LEFT OUTER JOIN code_mapper.v_concept destination ON m.destination_concept_id = destination.concept_id
     JOIN code_mapper.v_user u ON m.user_id = u.user_id
     JOIN code_mapper.event_type as et on m.event_type_id = et.event_type_id
     LEFT OUTER JOIN code_mapper.dialect as dd on m.destination_dialect_id = dd.dialect_id;



-- View: code_mapper.v_mapping_statistics

CREATE OR REPLACE VIEW code_mapper.v_mapping_statistics AS 
 SELECT v_mapping.source_organisation_id,
    v_mapping.source_organisation_name,
    v_mapping.source_dialect_id,
    v_mapping.source_dialect_name,
    v_mapping.source_code_system_id,
    v_mapping.source_code_system_name,
    v_mapping.destination_organisation_id,
    v_mapping.destination_organisation_name,
    v_mapping.destination_dialect_id,
    v_mapping.destination_dialect_name,
    v_mapping.destination_code_system_id,
    v_mapping.destination_code_system_name,
    count(*) AS count
   FROM code_mapper.v_mapping
  GROUP BY v_mapping.source_organisation_id, v_mapping.source_organisation_name, v_mapping.source_dialect_id, v_mapping.source_dialect_name, v_mapping.source_code_system_id, v_mapping.source_code_system_name, v_mapping.destination_organisation_id, v_mapping.destination_organisation_name, v_mapping.destination_dialect_id, v_mapping.destination_dialect_name, v_mapping.destination_code_system_id, v_mapping.destination_code_system_name;




