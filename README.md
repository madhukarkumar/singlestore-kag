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
   EMBEDDING_MODEL=text-embedding-3-large

   # SingleStore Configuration
   SINGLESTORE_HOST=your_host
   SINGLESTORE_PORT=3306
   SINGLESTORE_USER=your_username
   SINGLESTORE_PASSWORD=your_password
   SINGLESTORE_DATABASE=your_database
   ```

## Usage

The application provides several command-line options for processing documents:

```bash
# Process a document (PDF or markdown) and create embeddings
python main.py input_file --document_id ID

# Only create chunks without generating embeddings
python main.py input_file --document_id ID --chunks_only

# Store existing embeddings from a JSON file into SingleStore
python main.py input_file --document_id ID --store_embeddings
```

### Command Line Arguments

- `input_file`: Path to the input document (PDF or markdown)
- `--document_id`: Unique identifier for the document (required)
- `--chunks_only`: Only create chunks, don't generate embeddings
- `--store_embeddings`: Store existing embeddings from JSON file into SingleStore

### Examples

```bash
# Process a PDF document
python main.py documents/sample.pdf --document_id 1

# Process an existing markdown file
python main.py documents/sample.md --document_id 2

# Only create chunks from a PDF
python main.py documents/sample.pdf --document_id 3 --chunks_only

# Store embeddings from an existing JSON file
python main.py documents/sample.md --document_id 4 --store_embeddings
```

Note: When using `--store_embeddings`, the tool expects to find a JSON file with the same name as your input file but with `_embeddings.json` suffix. For example, if your input file is `sample.md`, it will look for `sample_embeddings.json`.

### 1. Step-by-Step Processing

Process documents one step at a time:

```bash
# 1. Convert PDF to markdown and create chunks
python main.py --pdf path/to/document.pdf --document_id 1

# 2. Process existing markdown file
python main.py --markdown path/to/document.md --document_id 1
```

### 2. End-to-End Workflow

Process documents through the complete pipeline:

```bash
python run_workflow.py --input path/to/document.pdf --document_id 1
```

### 3. Programmatic Usage

```python
from main import DocumentProcessor

# Initialize processor
processor = DocumentProcessor()

# Process a document
results = processor.process_document("document.pdf", document_id=1)

print(f"Processed {results['chunks_count']} chunks")
print(f"Markdown file: {results['markdown_path']}")
print(f"Embeddings file: {results['embeddings_path']}")
```

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

2. **Embedding Models**
   - Default model: `text-embedding-3-large` (3072 dimensions)
   - Legacy model: `text-embedding-ada-002` (1536 dimensions)
   - Always verify vector dimensions match database schema

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
[ ] Use Open AI to create Knowledge Graph in JSON
[ ] Store Knowledge Graph in SingleStore
[ ] Create small test to query across Knowledge Graph and embeddings
[ ] Create API endpoint to query knowledge graph
[ ] Create API endpoint to insert document into database
