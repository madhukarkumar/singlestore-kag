CREATE TABLE Document_Embeddings (
  embedding_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  doc_id       BIGINT NOT NULL,
  content      TEXT,
  embedding    VECTOR(1536),
  SORT KEY(),  -- Ensure this is a columnstore table&#8203;:contentReference[oaicite:11]{index=11}
  FULLTEXT USING VERSION 2 content_ft_idx (content),  -- Full-Text index (v2) on content&#8203;:contentReference[oaicite:12]{index=12}
  VECTOR INDEX embedding_vec_idx (embedding)          -- Vector index on embedding column&#8203;:contentReference[oaicite:13]{index=13}
    INDEX_OPTIONS '{ "index_type": "HNSW_FLAT", "metric_type": "DOT_PRODUCT" }'
);

ALTER TABLE Entities
  ADD FULLTEXT USING VERSION 2 ft_idx_name (name);

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
    SHARD KEY (entity_id, name),
    -- Add FULLTEXT index for name search
    FULLTEXT USING VERSION 2 name_ft_idx (name)
);

CREATE TABLE ProcessingStatus (
    doc_id BIGINT PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL UNIQUE,
    file_path VARCHAR(512) NOT NULL,
    file_size BIGINT NOT NULL,
    current_step ENUM('started', 'chunking', 'embeddings', 'entities', 'relationships', 'completed', 'failed') NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES Documents(doc_id) ON DELETE CASCADE
);

SHOW INDEXES FROM Document_Embeddings;

OPTIMIZE TABLE Document_Embeddings FLUSH;  -- Ensure recent data is indexed

SELECT
    doc_id,
    content,
    MATCH (TABLE Document_Embeddings) AGAINST ('How does SingleStore support hybrid search in RAG?') AS score
FROM Document_Embeddings
WHERE MATCH (TABLE Document_Embeddings) AGAINST ('How does SingleStore support hybrid search in RAG?')
ORDER BY score DESC
LIMIT 10;