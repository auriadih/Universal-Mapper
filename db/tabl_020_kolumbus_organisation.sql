-- Table: snomed.kolumbus_organisation

-- DROP TABLE snomed.kolumbus_organisation;

CREATE TABLE snomed.kolumbus_organisation
(
  organisation_id bigint NOT NULL DEFAULT nextval('snomed.kolumbus_orgn_seq'::regclass),
  organisation_name character varying NOT NULL,
  insert_ts timestamp without time zone NOT NULL DEFAULT now(),
  update_ts timestamp without time zone
)
WITH (
  OIDS=FALSE
);
