CREATE TABLE Document_Embeddings (
  embedding_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  doc_id BIGINT NOT NULL,               -- references Documents.doc_id (not enforced)
  content TEXT,                         -- textual content for full-text search
  embedding VECTOR(1536),               -- high-dimensional embedding vector (F32 elements by default)&#8203;:contentReference[oaicite:10]{index=10}
  FULLTEXT USING VERSION 2 content_ft_idx (content)  -- full-text index on content&#8203;:contentReference[oaicite:11]{index=11}&#8203;:contentReference[oaicite:12]{index=12}
);
ALTER TABLE Document_Embeddings
  ADD VECTOR INDEX idx_vec (embedding) 
    INDEX_OPTIONS '{"index_type": "HNSW_FLAT", "metric_type": "EUCLIDEAN_DISTANCE"}';


CREATE TABLE Documents (
  doc_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(255),
  author VARCHAR(100),
  publish_date DATE,
  source VARCHAR(255)
  -- Other metadata fields (e.g. summary, URL) can be added as needed
);

CREATE TABLE Relationships (
  relationship_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  source_entity_id BIGINT NOT NULL,
  target_entity_id BIGINT NOT NULL,
  relation_type VARCHAR(100),
  doc_id BIGINT,   -- reference to Documents.doc_id (not an enforced foreign key)
  KEY (source_entity_id) USING HASH,  -- index for quickly finding relationships by source
  KEY (target_entity_id) USING HASH,  -- index for quickly finding relationships by target
  KEY (doc_id)                      -- index for querying relationships by document
);

 CREATE TABLE Entities (
    entity_id BIGINT NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    aliases JSON,
    category VARCHAR(100),
    -- Make the primary key composite to include the shard key columns:
    PRIMARY KEY (entity_id, name),
    -- Shard key now includes the name column for local uniqueness enforcement:
    SHARD KEY (entity_id, name)
    -- We have effectively included `name` in the primary key, satisfying the 
    -- unique constraint requirement on name under SingleStore's rules.
);
