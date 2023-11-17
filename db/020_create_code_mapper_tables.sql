
CREATE SEQUENCE code_mapper.event_type__seq;

CREATE TABLE code_mapper.event_type (
                event_type_id BIGINT NOT NULL DEFAULT nextval('code_mapper.event_type__seq'),
                name VARCHAR NOT NULL,
                insert_ts TIMESTAMP DEFAULT now() NOT NULL,
                update_ts TIMESTAMP,
                CONSTRAINT event_type_pk PRIMARY KEY (event_type_id)
);
COMMENT ON TABLE code_mapper.event_type IS 'options are: incorrect concept; no match for concept in target dialect; bridge mapping; user mapping';


ALTER SEQUENCE code_mapper.event_type__seq OWNED BY code_mapper.event_type.event_type_id;

CREATE SEQUENCE code_mapper.group__seq;

CREATE TABLE code_mapper.group (
                group_id BIGINT NOT NULL DEFAULT nextval('code_mapper.group__seq'),
                name VARCHAR NOT NULL,
                insert_ts TIMESTAMP DEFAULT now() NOT NULL,
                update_ts TIMESTAMP,
                CONSTRAINT group_pk PRIMARY KEY (group_id)
);
COMMENT ON TABLE code_mapper.group IS 'admin, organisation_admin, normal';


ALTER SEQUENCE code_mapper.group__seq OWNED BY code_mapper.group.group_id;

CREATE SEQUENCE code_mapper.term__seq;

CREATE TABLE code_mapper.term (
                term_id BIGINT NOT NULL DEFAULT nextval('code_mapper.term__seq'),
                term_text VARCHAR NOT NULL,
                insert_ts TIMESTAMP DEFAULT now() NOT NULL,
                update_ts TIMESTAMP,
                CONSTRAINT term_pk PRIMARY KEY (term_id)
);


ALTER SEQUENCE code_mapper.term__seq OWNED BY code_mapper.term.term_id;

CREATE UNIQUE INDEX term_idx
 ON code_mapper.term
 ( term_text );

CREATE SEQUENCE code_mapper.code__seq;

CREATE TABLE code_mapper.code (
                code_id BIGINT NOT NULL DEFAULT nextval('code_mapper.code__seq'),
                code_text VARCHAR NOT NULL,
                insert_ts TIMESTAMP DEFAULT now() NOT NULL,
                update_ts TIMESTAMP,
                CONSTRAINT code_pk PRIMARY KEY (code_id)
);


ALTER SEQUENCE code_mapper.code__seq OWNED BY code_mapper.code.code_id;

CREATE UNIQUE INDEX code_idx
 ON code_mapper.code
 ( code_text );

CREATE SEQUENCE code_mapper.organization__seq;

CREATE TABLE code_mapper.organisation (
                organisation_id BIGINT NOT NULL DEFAULT nextval('code_mapper.organization__seq'),
                name VARCHAR NOT NULL,
                city VARCHAR NOT NULL,
                country VARCHAR NOT NULL,
                insert_ts TIMESTAMP DEFAULT now() NOT NULL,
                update_ts TIMESTAMP,
                CONSTRAINT organisation_pk PRIMARY KEY (organisation_id)
);
COMMENT ON TABLE code_mapper.organisation IS 'e.g. Auria, VSSHP,  Borealis, OYS, HUS, IHTSDO, etc.';


ALTER SEQUENCE code_mapper.organization__seq OWNED BY code_mapper.organisation.organisation_id;

CREATE SEQUENCE code_mapper.code_system__seq;

CREATE TABLE code_mapper.code_system (
                code_system_id BIGINT NOT NULL DEFAULT nextval('code_mapper.code_system__seq'),
                name VARCHAR NOT NULL,
                version VARCHAR,
                owner_organisation_id BIGINT NOT NULL,
                insert_ts TIMESTAMP DEFAULT now() NOT NULL,
                update_ts TIMESTAMP,
                CONSTRAINT code_system_pk PRIMARY KEY (code_system_id)
);
COMMENT ON TABLE code_mapper.code_system IS 'e.g. Snomed II, Snomed, CT, etc';


ALTER SEQUENCE code_mapper.code_system__seq OWNED BY code_mapper.code_system.code_system_id;

CREATE UNIQUE INDEX code_system_idx
 ON code_mapper.code_system
 ( name, version );

CREATE SEQUENCE code_mapper.dialect__seq;

CREATE TABLE code_mapper.dialect (
                dialect_id BIGINT NOT NULL DEFAULT nextval('code_mapper.dialect__seq'),
                code_system_id BIGINT NOT NULL,
                dialect_name VARCHAR NOT NULL,
                is_official BOOLEAN NOT NULL,
                insert_ts TIMESTAMP DEFAULT now() NOT NULL,
                update_ts TIMESTAMP,
                CONSTRAINT dialect_pk PRIMARY KEY (dialect_id)
);


ALTER SEQUENCE code_mapper.dialect__seq OWNED BY code_mapper.dialect.dialect_id;

CREATE SEQUENCE code_mapper.synonym__seq;

CREATE TABLE code_mapper.synonym (
                synonym_id BIGINT NOT NULL DEFAULT nextval('code_mapper.synonym__seq'),
                code_id BIGINT NOT NULL,
                synonym VARCHAR NOT NULL,
                dialect_id BIGINT NOT NULL,
                insert_ts TIMESTAMP DEFAULT now() NOT NULL,
                update_ts TIMESTAMP,
                CONSTRAINT synonym_pk PRIMARY KEY (synonym_id)
);


ALTER SEQUENCE code_mapper.synonym__seq OWNED BY code_mapper.synonym.synonym_id;

CREATE UNIQUE INDEX synonym_idx
 ON code_mapper.synonym
 ( code_id, synonym );

CREATE SEQUENCE code_mapper.concept__seq;

CREATE TABLE code_mapper.concept (
                concept_id BIGINT NOT NULL DEFAULT nextval('code_mapper.concept__seq'),
                code_id BIGINT NOT NULL,
                term_id BIGINT NOT NULL,
                organisation_id BIGINT NOT NULL,
                dialect_id BIGINT NOT NULL,
                insert_ts TIMESTAMP DEFAULT now() NOT NULL,
                update_ts TIMESTAMP,
                CONSTRAINT concept_pk PRIMARY KEY (concept_id)
);


ALTER SEQUENCE code_mapper.concept__seq OWNED BY code_mapper.concept.concept_id;

CREATE SEQUENCE code_mapper.concept_metadata__seq;

CREATE TABLE code_mapper.concept_metadata (
                concept_metadata_id BIGINT NOT NULL DEFAULT nextval('code_mapper.concept_metadata__seq'),
                concept_id BIGINT NOT NULL,
                obs_number INTEGER,
                first_obs_date DATE,
                last_obs_date DATE,
                insert_ts TIMESTAMP DEFAULT now() NOT NULL,
                update_ts TIMESTAMP,
                CONSTRAINT concept_metadata_pk PRIMARY KEY (concept_metadata_id)
);


ALTER SEQUENCE code_mapper.concept_metadata__seq OWNED BY code_mapper.concept_metadata.concept_metadata_id;

CREATE SEQUENCE code_mapper.user__seq;

CREATE TABLE code_mapper.user (
                user_id BIGINT NOT NULL DEFAULT nextval('code_mapper.user__seq'),
                organisation_id BIGINT NOT NULL,
                username VARCHAR,
                password_hash VARCHAR NOT NULL,
                email VARCHAR NOT NULL,
                last_name VARCHAR NOT NULL,
                first_name VARCHAR NOT NULL,
                default_source_dialect_id BIGINT,
                default_destination_dialect_id BIGINT,
                insert_ts TIMESTAMP DEFAULT now() NOT NULL,
                update_ts TIMESTAMP,
                CONSTRAINT user_pk PRIMARY KEY (user_id)
);
COMMENT ON TABLE code_mapper.user IS 'one user can be "automatic process", if automatic process has done the mapping of the term';


ALTER SEQUENCE code_mapper.user__seq OWNED BY code_mapper.user.user_id;

CREATE TABLE code_mapper.user_concept_note (
                user_id BIGINT NOT NULL,
                concept_id BIGINT NOT NULL,
                note TEXT NOT NULL,
                insert_ts TIMESTAMP DEFAULT now() NOT NULL,
                update_ts TIMESTAMP,
                CONSTRAINT user_concept_note_pk PRIMARY KEY (user_id, concept_id)
);
COMMENT ON COLUMN code_mapper.user_concept_note.note IS 'Note is not allowed to be null. Instead of setting the note to null, delete the whole row as obsolete.';


CREATE TABLE code_mapper.user_group (
                user_id BIGINT NOT NULL,
                group_id BIGINT NOT NULL,
                insert_ts TIMESTAMP DEFAULT now() NOT NULL,
                update_ts TIMESTAMP,
                CONSTRAINT user_group_pk PRIMARY KEY (user_id, group_id)
);


CREATE SEQUENCE code_mapper.session__seq;

CREATE TABLE code_mapper.session (
                session_id BIGINT NOT NULL DEFAULT nextval('code_mapper.session__seq'),
                user_id BIGINT NOT NULL,
                start_ts TIMESTAMP NOT NULL,
                end_ts TIMESTAMP,
                insert_ts TIMESTAMP DEFAULT now() NOT NULL,
                update_ts TIMESTAMP,
                CONSTRAINT session_pk PRIMARY KEY (session_id)
);


ALTER SEQUENCE code_mapper.session__seq OWNED BY code_mapper.session.session_id;

CREATE SEQUENCE code_mapper.mapping__seq;

CREATE TABLE code_mapper.mapping (
                mapping_id BIGINT NOT NULL DEFAULT nextval('code_mapper.mapping__seq'),
                valid BOOLEAN DEFAULT true NOT NULL,
                user_id BIGINT NOT NULL,
                session_id BIGINT NOT NULL,
                source_concept_id BIGINT NOT NULL,
                destination_concept_id BIGINT,
                destination_dialect_id BIGINT,
                event_type_id BIGINT NOT NULL,
                comment VARCHAR,
                insert_ts TIMESTAMP DEFAULT now() NOT NULL,
                update_ts TIMESTAMP,
                CONSTRAINT mapping_pk PRIMARY KEY (mapping_id)
);
COMMENT ON COLUMN code_mapper.mapping.valid IS 'whether this is the valid i.e. latest version of a mapping. When a row becomes invalid, it ends up in event_log as old_mapping_id.';
COMMENT ON COLUMN code_mapper.mapping.session_id IS 'the session in which this mapping was first created';
COMMENT ON COLUMN code_mapper.mapping.destination_concept_id IS 'can be null if event type is e.g. "concept is incorrect" or "concept has no equivalent in target dialect"';
COMMENT ON COLUMN code_mapper.mapping.destination_dialect_id IS 'can be null is event_type is e.g. "concept is incorrect". Is never null when event_type is e.g. "concept has no equivalent in target dialect", and should not be null if event_type is "user mapping" or "bridge mapping"';
COMMENT ON COLUMN code_mapper.mapping.update_ts IS 'changed when status of mapping changes, i.e. when mapping_status_id changes or mapping becomes valid or invalid';


ALTER SEQUENCE code_mapper.mapping__seq OWNED BY code_mapper.mapping.mapping_id;

ALTER TABLE code_mapper.mapping ADD CONSTRAINT event_type_mapping_fk
FOREIGN KEY (event_type_id)
REFERENCES code_mapper.event_type (event_type_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.user_group ADD CONSTRAINT group_user_group_fk
FOREIGN KEY (group_id)
REFERENCES code_mapper.group (group_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

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

ALTER TABLE code_mapper.synonym ADD CONSTRAINT code_synonym_fk
FOREIGN KEY (code_id)
REFERENCES code_mapper.code (code_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.user ADD CONSTRAINT organization_user_fk
FOREIGN KEY (organisation_id)
REFERENCES code_mapper.organisation (organisation_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.concept ADD CONSTRAINT organization_concept_fk
FOREIGN KEY (organisation_id)
REFERENCES code_mapper.organisation (organisation_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.code_system ADD CONSTRAINT organization_code_system_fk
FOREIGN KEY (owner_organisation_id)
REFERENCES code_mapper.organisation (organisation_id)
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

ALTER TABLE code_mapper.synonym ADD CONSTRAINT dialect_synonym_fk
FOREIGN KEY (dialect_id)
REFERENCES code_mapper.dialect (dialect_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.user ADD CONSTRAINT dialect_user_fk
FOREIGN KEY (default_source_dialect_id)
REFERENCES code_mapper.dialect (dialect_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.user ADD CONSTRAINT dialect_user_fk1
FOREIGN KEY (default_destination_dialect_id)
REFERENCES code_mapper.dialect (dialect_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.concept_metadata ADD CONSTRAINT concept_concept_metadata_fk
FOREIGN KEY (concept_id)
REFERENCES code_mapper.concept (concept_id)
ON DELETE CASCADE
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

ALTER TABLE code_mapper.user_concept_note ADD CONSTRAINT concept_user_concept_note_fk
FOREIGN KEY (concept_id)
REFERENCES code_mapper.concept (concept_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.mapping ADD CONSTRAINT user_mapping_fk
FOREIGN KEY (user_id)
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

ALTER TABLE code_mapper.user_group ADD CONSTRAINT user_user_group_fk
FOREIGN KEY (user_id)
REFERENCES code_mapper.user (user_id)
ON DELETE NO ACTION
ON UPDATE NO ACTION
NOT DEFERRABLE;

ALTER TABLE code_mapper.user_concept_note ADD CONSTRAINT user_user_concept_note_fk
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
