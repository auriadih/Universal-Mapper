-- Table: snomed.kolumbus_users

-- DROP TABLE snomed.kolumbus_users;

CREATE TABLE snomed.kolumbus_users
(
  user_id bigint NOT NULL DEFAULT nextval('snomed.kolumbus_user_seq'::regclass),
  first_name character varying NOT NULL,
  last_name character varying NOT NULL,
  username character varying NOT NULL,
  email character varying NOT NULL,
  organisation character varying NOT NULL,
  password_hash character varying,
  is_admin boolean NOT NULL,
  insert_ts timestamp without time zone NOT NULL DEFAULT now(),
  update_ts timestamp without time zone,
  CONSTRAINT kolumbus_user_pk PRIMARY KEY (user_id)
)
WITH (
  OIDS=FALSE
);
