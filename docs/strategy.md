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

The retrieval process handles user queries and returns relevant information using a hybrid search approach.

### 1. Query Processing (`rag_query.py`)
The query processing stage is the entry point for user interactions with our knowledge base. It implements a sophisticated RAG (Retrieval-Augmented Generation) approach that combines multiple search strategies to understand and process user queries effectively. This hybrid approach ensures both semantic understanding and precise matching of user intentions.

- **Class**: `RAGQueryEngine`
- **Key Methods**:
  - `query(query_text, top_k)`: Main entry point for search
  - Handles hybrid search combining vector and text similarity

**TODO - Potential Improvements**:
- Add query intent classification
- Implement query expansion using synonyms
- Add support for structured queries
- Implement query caching
- Add query preprocessing optimizations

### 2. Search Implementation
Our search implementation combines multiple search strategies to provide comprehensive and accurate results. The hybrid approach leverages both vector similarity for semantic understanding and text-based search for precise matching. This combination ensures that we capture both the meaning and the specific details in user queries.

- **Vector Search**:
  - Uses OpenAI embeddings for query encoding
  - Performs vector similarity search using HNSW index
  - Normalizes scores to 0-1 range

- **Text Search**:
  - Uses SingleStore Full-Text Search Version 2
  - Query format: `content:("query_text")`
  - TF-IDF based relevance scoring

- **Hybrid Scoring**:
  - Default weights: 70% vector, 30% text
  - Combines normalized scores
  - Configurable through search_config

**TODO - Potential Improvements**:
- Implement dynamic weight adjustment based on query type
- Add context-aware scoring adjustments
- Implement results diversity scoring
- Add support for semantic filters
- Implement approximate nearest neighbor search

### 3. Result Processing
The result processing phase enriches raw search results with additional context and relationships from our knowledge graph. This enrichment provides users with a more complete understanding of the information by including related entities, their descriptions, and interconnections. The process ensures that users receive not just matching text, but a rich context around their query.

- **Entity Enrichment**:
  - Adds relevant entities to search results
  - Includes entity metadata and descriptions
  - Maps relationships between entities

- **Response Generation**:
  - Context-aware prompt construction
  - Incorporates search results and entity relationships
  - Structured output with citations
  - Confidence scoring for responses

**TODO - Potential Improvements**:
- Add result clustering by topic
- Implement hierarchical result organization
- Add relevance feedback mechanism
- Enhance citation accuracy
- Implement answer validation

### 4. API Layer (`api.py`)
The API layer provides a clean and efficient interface for accessing our knowledge base. It implements RESTful endpoints that handle various types of queries and return well-structured responses. The API design focuses on flexibility and extensibility while maintaining consistent response formats and error handling.

- **Endpoints**:
  - `/kag-search`: Main search endpoint
  - Parameters: query, top_k, debug
  - Returns: SearchResponse with results, scores, and generated response

**TODO - Potential Improvements**:
- Add request rate limiting
- Implement response compression
- Add batch query support
- Implement async processing for large queries
- Add response streaming for large results

### 5. Response Models (`models.py`)
Our response models are designed to provide structured and consistent data formats for all API responses. They ensure type safety and data validation while maintaining flexibility for different types of search results and their associated metadata.

- **SearchResponse**:
  - Query text
  - List of SearchResults
  - Generated response
  - Execution time
  
- **SearchResult**:
  - Document content
  - Vector and text scores
  - Combined score
  - Related entities and relationships

**TODO - Potential Improvements**:
- Add response versioning support
- Implement partial response options
- Add response schema validation
- Enhance error reporting granularity
- Add support for custom response formats
