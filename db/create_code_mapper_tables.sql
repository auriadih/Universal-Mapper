
CREATE TABLE code_mapper.term (
                term_id BIGINT NOT NULL,
                term_text VARCHAR NOT NULL,
                CONSTRAINT term_pk PRIMARY KEY (term_id)
);


CREATE TABLE code_mapper.code (
                code_id BIGINT NOT NULL,
                code_text VARCHAR NOT NULL,
                CONSTRAINT code_pk PRIMARY KEY (code_id)
);


CREATE TABLE code_mapper.mapping_status (
                mapping_status_id BIGINT NOT NULL,
                name VARCHAR NOT NULL,
                CONSTRAINT mapping_status_pk PRIMARY KEY (mapping_status_id)
);
COMMENT ON TABLE code_mapper.mapping_status IS 'e.g. automatic match from bridge, manual match, bridge rejected by user';
COMMENT ON COLUMN code_mapper.mapping_status.mapping_status_id IS 'bridged, manually mapped, manually approved bridged, manually rejected bridged, etc.';


CREATE TABLE code_mapper.user (
                user_id BIGINT NOT NULL,
                organization_id BIGINT NOT NULL,
                username VARCHAR,
                password VARCHAR NOT NULL,
                email VARCHAR NOT NULL,
                last_name VARCHAR NOT NULL,
                first_name VARCHAR NOT NULL,
                CONSTRAINT user_pk PRIMARY KEY (user_id)
);
COMMENT ON TABLE code_mapper.user IS 'one user can be "automatic process", if automatic process has done the mapping of the term';


CREATE TABLE code_mapper.session (
                session_id BIGINT NOT NULL,
                start_ts TIMESTAMP NOT NULL,
                end_ts TIMESTAMP,
                user_id BIGINT NOT NULL,
                CONSTRAINT session_pk PRIMARY KEY (session_id)
);


CREATE TABLE code_mapper.organization (
                organization_id BIGINT NOT NULL,
                name VARCHAR NOT NULL,
                city VARCHAR NOT NULL,
                contact_user_id BIGINT,
                CONSTRAINT organization_pk PRIMARY KEY (organization_id)
);
COMMENT ON TABLE code_mapper.organization IS 'e.g. Auria, VSSHP,  Borealis, OYS, HUS, IHTSDO, etc.';


CREATE TABLE code_mapper.code_system (
                code_system_id BIGINT NOT NULL,
                name VARCHAR NOT NULL,
                version VARCHAR NOT NULL,
                owner_organization_id BIGINT NOT NULL,
                CONSTRAINT code_system_pk PRIMARY KEY (code_system_id)
);
COMMENT ON TABLE code_mapper.code_system IS 'e.g. Snomed II, Snomed, CT, etc';


CREATE TABLE code_mapper.dialect (
                dialect_id BIGINT NOT NULL,
                code_system_id BIGINT NOT NULL,
                dialect_name VARCHAR NOT NULL,
                CONSTRAINT dialect_pk PRIMARY KEY (dialect_id)
);


CREATE TABLE code_mapper.concept (
                concept_id BIGINT NOT NULL,
                code_id BIGINT NOT NULL,
                term_id BIGINT NOT NULL,
                organization_id BIGINT NOT NULL,
                dialect_id BIGINT NOT NULL,
                CONSTRAINT concept_pk PRIMARY KEY (concept_id)
);


CREATE TABLE code_mapper.concept_status (
                concept_status_id BIGINT NOT NULL,
                status_text VARCHAR NOT NULL,
                concept_id BIGINT NOT NULL,
                CONSTRAINT concept_status_pk PRIMARY KEY (concept_status_id)
);
COMMENT ON TABLE code_mapper.concept_status IS 'only bridged, mapped in my organization, mapped in other organization, etc.';


CREATE TABLE code_mapper.concept_metadata (
                concept_metadata_id BIGINT NOT NULL,
                concept_id BIGINT NOT NULL,
                obs_number INTEGER,
                first_obs_date DATE,
                last_obs_date DATE,
                CONSTRAINT concept_metadata_pk PRIMARY KEY (concept_metadata_id)
);


CREATE TABLE code_mapper.mapping (
                mapping_id BIGINT NOT NULL,
                valid BOOLEAN NOT NULL,
                user_id BIGINT NOT NULL,
                session_id BIGINT NOT NULL,
                mapping_status_id BIGINT NOT NULL,
                insert_ts TIMESTAMP NOT NULL,
                update_ts TIMESTAMP NOT NULL,
                source_concept_id BIGINT NOT NULL,
                destination_concept_id BIGINT NOT NULL,
                CONSTRAINT mapping_pk PRIMARY KEY (mapping_id)
);
COMMENT ON COLUMN code_mapper.mapping.valid IS 'whether this is the valid i.e. latest version of a mapping. When a row becomes invalid, it ends up in event_log as old_mapping_id.';
COMMENT ON COLUMN code_mapper.mapping.session_id IS 'the session in which this mapping was first created';
COMMENT ON COLUMN code_mapper.mapping.update_ts IS 'changed when status of mapping changes, i.e. when mapping_status_id changes or mapping becomes valid or invalid';


CREATE TABLE code_mapper.event_log (
                event_id BIGINT NOT NULL,
                old_mapping_id BIGINT NOT NULL,
                new_mapping_id BIGINT,
                explanation VARCHAR,
                CONSTRAINT event_log_pk PRIMARY KEY (event_id)
);
COMMENT ON TABLE code_mapper.event_log IS 'stores all changes made to existing mappings, i.e. when one mapping becomes invalid and a new mapping row is created in its place';
COMMENT ON COLUMN code_mapper.event_log.new_mapping_id IS 'this can be null if an old_mapping_id was discarded but no new mapping was created in its place';


ALTER TABLE code_mapper.concept ADD CONSTRAINT term_concept_fk
FOREIGN KEY (term_id)
REFERENCES code_mapper.term (term_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.concept ADD CONSTRAINT code_concept_fk
FOREIGN KEY (code_id)
REFERENCES code_mapper.code (code_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.mapping ADD CONSTRAINT mapping_type_mapping_fk
FOREIGN KEY (mapping_status_id)
REFERENCES code_mapper.mapping_status (mapping_status_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.mapping ADD CONSTRAINT user_mapping_fk
FOREIGN KEY (user_id)
REFERENCES code_mapper.user (user_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.organization ADD CONSTRAINT user_organization_fk
FOREIGN KEY (contact_user_id)
REFERENCES code_mapper.user (user_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.session ADD CONSTRAINT user_session_fk
FOREIGN KEY (user_id)
REFERENCES code_mapper.user (user_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.mapping ADD CONSTRAINT session_mapping_fk
FOREIGN KEY (session_id)
REFERENCES code_mapper.session (session_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.user ADD CONSTRAINT organization_user_fk
FOREIGN KEY (organization_id)
REFERENCES code_mapper.organization (organization_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.concept ADD CONSTRAINT organization_concept_fk
FOREIGN KEY (organization_id)
REFERENCES code_mapper.organization (organization_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.code_system ADD CONSTRAINT organization_code_system_fk
FOREIGN KEY (owner_organization_id)
REFERENCES code_mapper.organization (organization_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.dialect ADD CONSTRAINT code_system_dialect_fk
FOREIGN KEY (code_system_id)
REFERENCES code_mapper.code_system (code_system_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.concept ADD CONSTRAINT dialect_concept_fk
FOREIGN KEY (dialect_id)
REFERENCES code_mapper.dialect (dialect_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.concept_metadata ADD CONSTRAINT concept_concept_metadata_fk
FOREIGN KEY (concept_id)
REFERENCES code_mapper.concept (concept_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.concept_status ADD CONSTRAINT concept_concept_status_fk
FOREIGN KEY (concept_id)
REFERENCES code_mapper.concept (concept_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.mapping ADD CONSTRAINT concept_mapping_fk
FOREIGN KEY (source_concept_id)
REFERENCES code_mapper.concept (concept_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.mapping ADD CONSTRAINT concept_mapping_fk1
FOREIGN KEY (destination_concept_id)
REFERENCES code_mapper.concept (concept_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.event_log ADD CONSTRAINT mapping_event_log_fk
FOREIGN KEY (old_mapping_id)
REFERENCES code_mapper.mapping (mapping_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.event_log ADD CONSTRAINT mapping_event_log_fk1
FOREIGN KEY (new_mapping_id)
REFERENCES code_mapper.mapping (mapping_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;
