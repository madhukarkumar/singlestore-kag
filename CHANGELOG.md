# Changelog

## [1.0.0] - 2025-02-11 21:37 PST

### Added
- Hybrid search implementation combining vector similarity and full-text search
- Vector search using SingleStore's DOT_PRODUCT operator and session variables
- Full-text search using SingleStore's MATCH AGAINST functionality
- Score normalization and weighted combination of vector and text scores
- Debug output mode for troubleshooting and analysis
- Configurable search parameters:
  - Vector similarity threshold
  - Vector/text weight balance
  - Result limit (top_k)
  - Context window size

### Changed
- Refactored RAGQueryEngine to separate vector and text search methods
- Improved vector parameter handling in SingleStore queries
- Enhanced error handling and logging throughout the system
- Updated response generation to include entity and relationship context

### Fixed
- Vector embedding parameter formatting for SingleStore compatibility
- Result tuple to dictionary conversion for proper JSON serialization
- Context window retrieval for adjacent chunks
- Entity and relationship extraction error handling

### Technical Details
- Vector Search:
  - Uses OpenAI's text-embedding-ada-002 model
  - Implements proper vector formatting for SingleStore's VECTOR(1536) type
  - Session variable approach for reliable vector parameter handling
  
- Text Search:
  - Utilizes SingleStore's Full-Text Search Version 2
  - Implements content-based relevance scoring
  - Supports natural language queries
  
- Result Merging:
  - Score normalization for vector and text results
  - Configurable weighting between vector and text scores
  - Deduplication and sorting by combined score

### Development Notes
- Environment: Python 3.12.9
- Key Dependencies:
  - OpenAI API for embeddings
  - SingleStore for vector and text search
  - FastAPI for REST endpoints
