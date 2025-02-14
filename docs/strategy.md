# Knowledge Base Strategy

## Section 1 - Knowledge Creation

The knowledge creation process involves transforming raw documents into a structured knowledge base with semantic chunks, embeddings, entities, and relationships. Here's the detailed workflow:

### 1. Document Processing (`main.py`)
The document processing stage serves as the foundation of our knowledge creation pipeline. It handles the initial ingestion of documents, converting them from their original format (such as PDF) into a structured format that can be processed further. This stage ensures that document structure, formatting, and content hierarchy are preserved while preparing the content for semantic analysis.

- **Class**: `DocumentProcessor`
- **Key Methods**:
  - `process_document(input_path, document_id)`: Main entry point for document processing
  - `get_chunks(pdf_path)`: Converts PDF to markdown with semantic chunks
  - `create_embeddings(input_markdown_file, output_json_file)`: Generates embeddings for chunks

**TODO - Potential Improvements**:
- Add support for table structure preservation in PDF conversion
- Implement parallel processing for large documents
- Add OCR capabilities for scanned documents
- Cache intermediate results for faster reprocessing
- Add validation step to detect and handle malformed documents early

### 2. Semantic Chunking
Our semantic chunking strategy goes beyond simple text splitting by understanding and preserving the document's semantic structure. Using advanced AI models, we ensure that related content stays together, section hierarchies are maintained, and context is preserved across chunk boundaries. This intelligent chunking is crucial for maintaining the document's meaning and relationships in later processing stages.

- **Configuration**: `ChunkingConfig` in `api.py`
- **Key Parameters**:
  - Semantic rules for preserving document structure
  - Overlap size for context preservation
  - Min/max chunk sizes
- **Implementation**:
  - Uses Gemini AI for semantic chunking
  - Preserves section headers and relationships
  - Maintains feature lists and technical concepts
  - Falls back to basic chunking if needed

**TODO - Potential Improvements**:
- Add adaptive chunk sizing based on content complexity
- Implement caching for frequently used chunk patterns
- Add support for domain-specific chunking rules
- Enhance fallback chunking with better heuristics
- Add chunk quality validation metrics

### 3. Embedding Generation
The embedding generation phase transforms our text chunks into high-dimensional vector representations that capture semantic meaning. We use state-of-the-art language models to create these embeddings, ensuring that similar concepts are mapped to similar vector spaces. This vectorization enables efficient semantic search and similarity comparisons.

- **Model**: OpenAI's text-embedding-ada-002
- **Process**:
  - Generates 1536-dimensional vectors for each chunk
  - Normalizes and formats embeddings for database storage
  - Stores in Document_Embeddings table with HNSW index

**TODO - Potential Improvements**:
- Implement batch processing for embedding generation
- Add embedding model fallback options
- Implement embedding caching for identical chunks
- Add embedding quality metrics
- Optimize vector dimensionality for storage efficiency

### 4. Knowledge Graph Generation (`knowledge_graph.py`)
The knowledge graph generation phase enriches our document understanding by identifying and connecting key entities and their relationships. This creates a rich semantic network that captures the interconnections between different concepts, people, organizations, and other entities mentioned in the documents. The resulting graph structure enables complex query understanding and relationship-based insights.

- **Class**: `KnowledgeGraphGenerator`
- **Key Methods**:
  - `process_document(doc_id)`: Processes all chunks from a document
  - `extract_knowledge_sync(text)`: Extracts entities and relationships
- **Entity Extraction**:
  - Uses OpenAI for entity and relationship extraction
  - Configurable confidence thresholds
  - Entity categories: PERSON, ORGANIZATION, LOCATION, TECHNOLOGY, CONCEPT, EVENT, PRODUCT
  - Stores metadata about extraction quality

**TODO - Potential Improvements**:
- Add entity disambiguation using context
- Implement relationship confidence scoring
- Add support for custom entity types
- Enhance entity linking across documents
- Add temporal relationship tracking

### 5. Database Storage
Our database storage strategy is optimized for both performance and flexibility. We use a distributed database architecture with specialized indexes for different types of queries. The schema design carefully balances normalization with query performance, while the indexing strategy ensures fast retrieval for both vector similarity and text-based searches.

- **Tables**:
  - `Document_Embeddings`: Chunks and vector embeddings
  - `Documents`: Document metadata
  - `Entities`: Extracted entities with metadata
  - `Relationships`: Entity relationships and graph structure
- **Indexes**:
  - HNSW_FLAT vector index for embeddings
  - FULLTEXT VERSION 2 for text search
  - HASH indexes for relationship lookups

**TODO - Potential Improvements**:
- Implement materialized views for common queries
- Add chunk-level caching layer
- Optimize index parameters based on usage patterns
- Add support for versioned embeddings
- Implement automated index maintenance

## Database Structure and Queries

### Entity-Document Relationships
- Entities are stored in the `Entities` table with their core attributes
- Document-Entity relationships are tracked through the `Relationships` table
- Each relationship links:
  - Source entity (source_entity_id)
  - Target entity (target_entity_id)
  - Document context (doc_id)
  - Relationship type

### Statistics Computation
- Document chunks are counted from distinct `embedding_id`s in `Document_Embeddings`
- Entity counts per document are derived from relationships where the entity appears as source or target
- Relationship counts are directly queried from the `Relationships` table by `doc_id`

This structure ensures:
- Clean separation of entity definitions from their document contexts
- Accurate tracking of entity appearances across documents
- Efficient querying of document-specific statistics
- Proper handling of entity relationships and their document context

## Section 2 - Knowledge Retrieval

The retrieval process implements a sophisticated RAG (Retrieval-Augmented Generation) approach that combines multiple search strategies:

### 1. Query Processing
- **Query Preprocessing**:
  - Special character handling
  - Whitespace normalization
  - Quoted phrase preservation
  
- **Query Expansion**:
  - LLM-based concept extraction
  - Synonym expansion
  - Configurable model selection (OpenAI/Groq)

### 2. Search Implementation

#### Vector Search
- **Model**: OpenAI text-embedding-ada-002
- **Implementation**:
  - 1536-dimensional vectors
  - Cosine similarity via SingleStore vector operations
  - Early exit optimization for high confidence matches
  - Configurable result limits

#### Text Search
- **Engine**: SingleStore Full-Text Search Version 2
- **Features**:
  - Exact phrase matching with boosted weights
  - Proximity search for term groups
  - Individual term weighting
  - Configurable distance parameters

#### Hybrid Search
- **Score Combination**:
  - Default weights: 70% vector, 30% text
  - Score normalization for fair combination
  - Configurable minimum score thresholds
  - Result deduplication
  - Dynamic weight adjustment based on query type

### 3. Result Enhancement
- **Entity Enrichment**:
  - Entity extraction for each result
  - Entity metadata inclusion
  - Category-based organization

- **Relationship Mapping**:
  - Entity relationship discovery
  - Graph-based context addition
  - Relationship type classification

- **Response Generation**:
  - Context-aware prompt construction
  - Configurable model selection (OpenAI/Groq)
  - Citation and source tracking
  - Confidence scoring

### 4. Performance Optimizations
- Early exit for high-confidence matches
- Batch processing for embeddings
- Efficient SQL query construction
- Score-based result filtering
- Caching of intermediate results

### 5. Configuration
All aspects of the retrieval process are configurable through YAML:
- Model selection and parameters
- Search weights and thresholds
- Result limits and scoring
- Response generation settings

This implementation ensures:
1. High accuracy through hybrid search
2. Fast retrieval via optimized indexes
3. Rich context through entity relationships
4. Flexible configuration for different use cases
