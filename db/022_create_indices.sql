
CREATE INDEX code_system_owner_organisation_id_idx ON code_mapper.code_system USING btree (owner_organisation_id);
CREATE INDEX concept_code_id_dialect_id_idx ON code_mapper.concept USING btree (code_id, dialect_id);
CREATE INDEX concept_dialect_id_idx ON code_mapper.concept USING btree (dialect_id);
CREATE INDEX concept_metadata_concept_id_idx ON code_mapper.concept_metadata USING btree (concept_id);
CREATE INDEX concept_organisation_id_idx ON code_mapper.concept USING btree (organisation_id);
CREATE INDEX concept_term_id_dialect_id_idx ON code_mapper.concept USING btree (term_id, dialect_id);
CREATE INDEX dialect_code_system_id_idx ON code_mapper.dialect USING btree (code_system_id);
CREATE INDEX mapping_destination_concept_id_idx ON code_mapper.mapping USING btree (destination_concept_id);
CREATE INDEX mapping_destination_dialect_id_idx ON code_mapper.mapping USING btree (destination_dialect_id);
CREATE INDEX mapping_event_type_id_idx ON code_mapper.mapping USING btree (event_type_id);
CREATE INDEX mapping_source_concept_id_idx ON code_mapper.mapping USING btree (source_concept_id);
CREATE INDEX synonym_dialect_id_idx ON code_mapper.synonym USING btree (dialect_id);
CREATE INDEX user_organisation_id_idx ON code_mapper."user" USING btree (organisation_id);



