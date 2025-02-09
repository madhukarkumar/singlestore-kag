# SingleStore Knowledge Graph Generator

A sophisticated Python application that processes documents (PDF/Markdown) to create semantic embeddings and knowledge graphs using OpenAI and Google's Gemini AI models. The extracted knowledge is stored in a SingleStore database, leveraging its vector search capabilities for efficient retrieval and querying.

## System Architecture

### Database Schema

The system uses four main tables in SingleStore:

1. **Document_Embeddings**
   - Stores document chunks and their vector embeddings
   - Uses HNSW vector index for efficient similarity search
   - Includes full-text search capabilities

2. **Documents**
   - Stores document metadata (title, author, date, etc.)
   - Acts as a parent table for document chunks

3. **Entities**
   - Stores extracted entities with their properties
   - Optimized for SingleStore's distributed architecture
   - Uses composite primary key for efficient sharding

4. **Relationships**
   - Captures relationships between entities
   - Links to source documents for provenance
   - Optimized with hash indexes for quick lookups

### Core Components

1. **Database Connection (db.py)**
   ```python
   from db import DatabaseConnection
   
   # Using context manager
   with DatabaseConnection() as db:
       db.execute_query("SELECT * FROM Documents")
   
   # Or manual connection management
   db = DatabaseConnection()
   db.connect()
   db.execute_query("SELECT * FROM Documents")
   db.disconnect()
   ```
   
   Key features:
   - Connection pooling and management
   - Error handling and logging
   - Table existence checks
   - Query execution with parameter binding

2. **Document Processor (main.py)**
   ```python
   from main import DocumentProcessor
   
   processor = DocumentProcessor()
   results = processor.process_document("document.pdf", document_id=1)
   ```
   
   Capabilities:
   - PDF to markdown conversion
   - Semantic chunking using Gemini AI
   - Embedding generation using OpenAI
   - Database integration

3. **Knowledge Graph Generator (knowledge_graph.py)**
   ```python
   from knowledge_graph import KnowledgeGraphGenerator
   
   generator = KnowledgeGraphGenerator()
   graph = generator.generate_knowledge_graph("document.pdf", document_id=1)
   ```
   
   Capabilities:
   - Entity extraction using OpenAI
   - Relationship extraction
   - Graph storage in SingleStore
   - Debug mode for local development

## Setup and Installation

1. **Python Environment**
   ```bash
   # Install Python 3.12.9
   pyenv install 3.12.9
   
   # Create virtual environment
   pyenv virtualenv 3.12.9 singlestore-kag-env
   pyenv activate singlestore-kag-env
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   # Connect to SingleStore and run schema
   mysql -h <host> -u <user> -p <database> < schema.sql
   ```

3. **Environment Configuration**
   Create a `.env` file:
   ```env
   # API Keys
   GEMINI_API_KEY=your_gemini_api_key
   OPENAI_API_KEY=your_openai_api_key
   PROJECT_ID=your_project_id
   EMBEDDING_MODEL=text-embedding-ada-002

   # SingleStore Configuration
   SINGLESTORE_HOST=your_host
   SINGLESTORE_PORT=3306
   SINGLESTORE_USER=your_username
   SINGLESTORE_PASSWORD=your_password
   SINGLESTORE_DATABASE=your_database
   ```

## Usage

The application provides several command-line options for different stages of document processing:

1. **Create Chunks from PDF**
   ```bash
   # Convert PDF to markdown with semantic chunks
   python main.py document.pdf --document_id 1 --chunks_only
   ```

2. **Create Embeddings from Markdown**
   ```bash
   # Generate embeddings from markdown file
   python main.py document.md --document_id 1 --create_embeddings
   ```

3. **Store Embeddings in SingleStore**
   ```bash
   # Store existing embeddings from JSON file
   python main.py document.md --document_id 1 --store_embeddings
   ```

4. **Full Processing Pipeline**
   ```bash
   # Process PDF end-to-end: chunks -> embeddings -> database
   python main.py document.pdf --document_id 1
   ```

5. **Knowledge Graph Generation**
   ```bash
   # Process a document and generate knowledge graph
   python knowledge_graph.py --doc_id 1

   # Process with debug output (saves JSON files locally)
   python knowledge_graph.py --doc_id 1 --debug
   ```

### Command Line Arguments

- `input_file`: Path to input document (PDF or markdown)
- `--document_id`: Unique identifier for the document (required)
- `--chunks_only`: Only create chunks, don't generate embeddings
- `--create_embeddings`: Create embeddings from an existing markdown file
- `--store_embeddings`: Store existing embeddings from JSON file into SingleStore
- `--debug`: Enable debug mode for local development

### Typical Workflow

1. Start with a PDF document:
   ```bash
   # First, create semantic chunks
   python main.py mydoc.pdf --document_id 1 --chunks_only
   
   # Then, create embeddings from the markdown
   python main.py mydoc.md --document_id 1 --create_embeddings
   
   # Finally, store embeddings in SingleStore
   python main.py mydoc.md --document_id 1 --store_embeddings
   
   # Generate knowledge graph
   python knowledge_graph.py --doc_id 1
   ```

2. Start with a markdown document:
   ```bash
   # Create embeddings from markdown
   python main.py mydoc.md --document_id 1 --create_embeddings
   
   # Store embeddings in SingleStore
   python main.py mydoc.md --document_id 1 --store_embeddings
   
   # Generate knowledge graph
   python knowledge_graph.py --doc_id 1
   ```

## SingleStore Full-Text Search Implementation

### Query Syntax

The system implements SingleStore's full-text search capabilities with the following syntax:

```sql
MATCH(TABLE table_name) AGAINST(search_expression)
```

Key implementation details:

1. **Column Prefixes**
   - Use `content:` prefix for searching document content
   - Use `name:` prefix for searching entity names
   - Example: `content:("how to use singlestore")`

2. **Query Formatting**
   - Wrap search terms in parentheses and quotes
   - Correct: `content:("search terms")`
   - Incorrect: `content:search terms` or `"content:(search terms)"`

3. **SQL Parameter Binding**
   ```python
   # Correct implementation
   formatted_query = f'content:("{query}")'
   sql = """
       SELECT *
       FROM Documents
       WHERE MATCH(TABLE Documents) AGAINST(%s)
   """
   db.execute_query(sql, (formatted_query,))
   ```

4. **Common Pitfalls**
   - Avoid manual quoting in SQL template (use %s without quotes)
   - Let database driver handle parameter quoting
   - Keep full-text index up to date for optimal performance

### Hybrid Search Implementation

The system combines three search approaches:
1. Vector similarity search using HNSW index
2. Full-text search using SingleStore's MATCH syntax
3. Knowledge graph traversal for related entities

This hybrid approach provides:
- Semantic understanding through vector search
- Keyword matching through full-text search
- Contextual relationships through graph traversal

## Project Status

### Completed Features 

1. **Document Processing**
   - PDF to markdown conversion with semantic chunking
   - Embedding generation using OpenAI (text-embedding-ada-002)
   - SingleStore vector database integration
   - Clear CLI interface with specific processing flags

2. **Database Integration**
   - Documents table for metadata
   - Document_Embeddings table with VECTOR(1536)
   - HNSW vector index for similarity search
   - Full-text search capabilities

3. **Technical Infrastructure**
   - Python 3.12.9 environment management
   - Comprehensive error handling and logging
   - Environment-based configuration
   - Modular code structure

4. **Knowledge Graph Generation** 
   - Design knowledge graph schema
   - Implement OpenAI-based entity extraction
   - Implement relationship extraction
   - Create graph storage in SingleStore
   - Debug mode for local development

### In Progress 

1. **Query Interface**
   - Design API endpoints
   - Implement hybrid search (vector + graph)
   - Create query optimization layer

2. **API Development**
   - Document insertion endpoint
   - Knowledge graph query endpoint
   - Vector similarity search endpoint

## Roadmap

### Phase 1: Document Processing 
- [x] Create semantic chunks from PDF using Gemini
- [x] Convert chunks to embeddings using OpenAI
- [x] Store embeddings in SingleStore
- [x] Implement proper dimension handling (1536D)

### Phase 2: Knowledge Graph 
- [x] Design knowledge graph schema
- [x] Create OpenAI prompts for graph extraction
- [x] Implement graph generation pipeline
- [x] Store and index graph in SingleStore

### Phase 3: Query Interface 
- [ ] Design REST API endpoints
- [ ] Implement vector similarity search
- [ ] Add knowledge graph traversal
- [ ] Create hybrid search capabilities

### Phase 4: Production Ready 
- [ ] Add authentication and rate limiting
- [ ] Implement caching layer
- [ ] Add monitoring and analytics
- [ ] Create deployment documentation

## API Reference

### DocumentProcessor Class

```python
class DocumentProcessor:
    def get_chunks(self, pdf_path: str) -> str:
        """Convert PDF to markdown with semantic chunks"""
        
    def create_embeddings(self, markdown_path: str) -> str:
        """Create embeddings for markdown chunks"""
        
    def insert_embeddings_to_db(self, embeddings_file: str, document_id: int) -> None:
        """Store embeddings in SingleStore"""
        
    def process_document(self, input_path: str, document_id: int) -> dict:
        """Complete end-to-end document processing"""
```

### DatabaseConnection Class

```python
class DatabaseConnection:
    def connect(self) -> None:
        """Establish database connection"""
        
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[List[Tuple]]:
        """Execute SQL query with parameters"""
        
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        
    def create_knowledge_graph_table(self) -> None:
        """Create knowledge graph table if not exists"""
```

## Lessons and Common Issues

### API Version Compatibility

1. **OpenAI API (1.0.0+)**
   - The OpenAI Python client underwent a major update in version 1.0.0
   - Key changes in embedding creation:
     ```python
     # Old syntax (<1.0.0)
     response = openai.Embedding.create(input=text, model="text-embedding-3-large")
     vector = response['data'][0]['embedding']

     # New syntax (1.0.0+)
     client = openai.OpenAI()
     response = client.embeddings.create(input=text, model="text-embedding-3-large")
     vector = response.data[0].embedding
     ```
   - Always use the OpenAI client instance for API calls
   - Reference: [OpenAI Migration Guide](https://github.com/openai/openai-python/discussions/742)

2. **Embedding Models and SingleStore Compatibility**
   - Using `text-embedding-ada-002` (1536 dimensions) to match schema
   - Schema configuration:
     ```sql
     -- In schema.sql
     embedding VECTOR(1536)  -- Matches text-embedding-ada-002 dimensions
     ```
   - SingleStore expects vectors as JSON arrays:
     ```python
     # Convert embedding to JSON array string
     embedding_json = json.dumps(embedding_list)
     
     # Insert into SingleStore
     db.execute("INSERT ... VALUES (%s)", embedding_json)
     ```
   - To use a different model, update both:
     1. The EMBEDDING_MODEL environment variable
     2. The VECTOR dimensions in schema.sql

### Document Processing

1. **Chunking Strategy**
   - Use Gemini's semantic chunking (250-1000 words)
   - Preserve chunks between `<chunk>` tags
   - Don't modify chunks before embedding to maintain semantic coherence

2. **File Processing**
   - PDF files are converted to markdown with semantic chunks
   - If a markdown file exists with the same name as the PDF, it will be used instead of reprocessing
   - This allows manual editing of chunks if needed before embedding
   - Example:
     ```
     # Input: document.pdf
     # If document.md exists, use it
     # Otherwise, process PDF to create document.md
     ```

## Development

### Logging

The application uses Python's logging module with two main levels:
- DEBUG: Detailed execution flow
- INFO: Important state changes and results

Example log output:
```
2025-02-08 10:55:42 [INFO] Reading PDF file: document.pdf
2025-02-08 10:55:43 [DEBUG] Found 5 chunks to process
2025-02-08 10:55:45 [INFO] Successfully inserted chunks into database
```

### Error Handling

The application implements comprehensive error handling:
- Database connection errors
- API failures (Gemini/OpenAI)
- File I/O errors
- Invalid input validation

### Testing

Run the database connection test:
```bash
python db.py
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT - See LICENSE file for details

## Acknowledgments

- OpenAI for embedding generation
- Google Gemini for semantic chunking
- SingleStore for vector database capabilities

## TODO
[x] Create semantic chunks from PDF using Gemini
[x] Convert chunks to embeddings in an md file using OpenAI
[x] Store embeddings in SingleStore
[x] Use Open AI to create Knowledge Graph in JSON
[x] Store Knowledge Graph in SingleStore
[ ] Create small test to query across Knowledge Graph and embeddings
[ ] Create API endpoint to query knowledge graph
[ ] Create API endpoint to insert document into database
