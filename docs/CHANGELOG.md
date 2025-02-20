# Changelog

## [1.1.0] - 2025-02-12

### Fixed
- Fixed Full-Text Search Version 2 query format:
  - Updated MATCH syntax to use `MATCH(TABLE table_name)` instead of column names
  - Added field specification in query strings (e.g., `content:term`)
  - Added proximity search support for multi-term queries
  - Properly formatted weight boosting with `>>` operator

### Added
- Added proximity search for multi-term queries to improve text search relevance
- Added comprehensive logging for search query construction and results

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

## [0.2.1] - 2025-02-12

### Added
- New configuration management page at `/config`
- API endpoints for retrieving and updating configuration settings
- Dynamic configuration for chunking, entity extraction, search, and response generation parameters

### Fixed
- Bug in graph visualization where nodes would reset position on mouse leave
- Fixed node sizes in graph visualization to be consistent (8px diameter)

### Changed
- Improved code organization by cleaning up configuration handling
- Updated API documentation to include configuration endpoints

## [0.2.0] - 2025-02-11
