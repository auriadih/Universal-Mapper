-- Table: snomed.kolumbus_mapping_status

-- DROP TABLE snomed.kolumbus_mapping_status;

CREATE TABLE snomed.kolumbus_mapping_status
(
  mapping_id bigint NOT NULL DEFAULT nextval('snomed.kolumbus_map_seq'::regclass),
  mapping_description character varying NOT NULL,
  insert_ts timestamp without time zone NOT NULL DEFAULT now(),
  update_ts timestamp without time zone
)
WITH (
  OIDS=FALSE
);
