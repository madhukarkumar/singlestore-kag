# SingleStore Prime Radian

A full-stack application that processes documents to create semantic embeddings and knowledge graphs using OpenAI and Google's Gemini AI models. The system uses SingleStore for storing and querying vector embeddings, document content, and knowledge graph relationships.

## Features

- **Document Processing**
  - PDF and Markdown document processing
  - Real-time progress tracking with detailed status updates
  - Semantic chunking using Google's Gemini AI
  - Vector embeddings using OpenAI's text-embedding-ada-002
  - Automatic knowledge graph generation
  - Asynchronous processing with Celery

- **Search Capabilities**
  - Hybrid search combining vector similarity and full-text search
  - Entity and relationship extraction
  - Natural language response generation
  - Fast and accurate document retrieval

- **Modern Web Interface**
  - Clean and responsive Next.js frontend
  - Real-time search results
  - Interactive progress tracking for document processing
  - Visual feedback for processing stages
  - Detailed result display with scores and entities
  - Mobile-friendly design

- **Knowledge Base Analytics**
  - Real-time statistics dashboard
  - Document-level metrics
  - Entity and relationship tracking
  - Interactive knowledge graph visualization
  - Chunk distribution analysis

## Version History

### v2.0.1 (2025-02-14)
- Fixed document statistics retrieval by correctly handling entity-document relationships
- Improved database query structure for accurate entity and relationship counting
- Enhanced stability of knowledge base statistics endpoint

### v2.0.0 (2025-02-13)
- Complete UI redesign with modern aesthetics
- New unified dashboard layout with statistics and search
- Improved navigation with consistent header across pages
- Dedicated knowledge base statistics page
- Enhanced upload experience with real-time feedback
- Streamlined search interface with better response display
- Mobile-responsive design improvements

### v1.2.0 (2025-02-11)
- Improved semantic chunking with structured Gemini prompts
- Enhanced document structure preservation
- Better handling of feature lists and technical content
- Improved search accuracy for technical queries

### v1.0.0 (2025-02-11)
- Stable release with production-ready features
- Optimized vector search using SingleStore session variables
- Enhanced hybrid search with configurable weights
- Improved error handling and debugging capabilities
- Comprehensive logging and error reporting
- Added detailed changelog (see CHANGELOG.md)

## Installation and Setup

### Prerequisites

- Python 3.12.9
- Node.js 18+ and pnpm
- SingleStore database
- OpenAI API key
- Google Gemini API key
- Redis (for Celery task queue)

### Backend Setup

1. **Environment Setup**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r backend/requirements.txt
   ```

2. **Environment Configuration**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_key
   GEMINI_API_KEY=your_gemini_key
   SINGLESTORE_HOST=your_host
   SINGLESTORE_PORT=your_port
   SINGLESTORE_USER=your_user
   SINGLESTORE_PASSWORD=your_password
   SINGLESTORE_DATABASE=your_database
   REDIS_URL=redis://localhost:6379/0
   ```

3. **Database Setup**
   ```bash
   # Initialize SingleStore schema
   mysql -h <host> -u <user> -p <database> < backend/db/schema.sql
   ```

4. **Start Backend Services**
   ```bash
   # Start Redis (if not already running)
   brew services start redis

   # Start all backend services
   ./start_backend_services.sh
   
   # API will be available at http://localhost:8000
   # Swagger docs at http://localhost:8000/docs
   ```

### Frontend Setup

1. **Install Dependencies**
   ```bash
   # Navigate to frontend directory
   cd frontend
   
   # Install packages
   pnpm install
   ```

2. **Start Development Server**
   ```bash
   pnpm dev
   # Frontend will be available at http://localhost:3000
   ```

## Project Structure

```
singlestore-kag/
├── backend/               # Backend application code
│   ├── api.py            # FastAPI endpoints
│   ├── db.py             # Database operations
│   ├── knowledge_graph.py # Knowledge graph generation
│   ├── pdf_processor.py  # PDF processing logic
│   ├── rag_query.py      # RAG implementation
│   ├── tasks.py          # Celery task definitions
│   ├── models.py         # Data models
│   ├── config.yaml       # Application configuration
│   └── requirements.txt  # Python dependencies
│
├── frontend/             # Next.js frontend application
│   ├── components/       # React components
│   ├── pages/           # Next.js pages
│   ├── styles/          # CSS and styling
│   └── package.json     # Frontend dependencies
│
└── docs/                # Documentation
    ├── api.md           # API documentation
    └── strategy.md      # Implementation strategy
```

## System Architecture

### Backend Components

1. **Document Processing Pipeline**
   - **PDF Processing (`pdf_processor.py`)**
     - PDF validation and text extraction
     - Progress tracking and status updates
     - Database record management
   
   - **Task Queue (`tasks.py`)**
     - Celery task definitions
     - Asynchronous processing
     - Progress reporting
   
   - **Knowledge Graph Generation (`knowledge_graph.py`)**
     - Entity and relationship extraction
     - Graph structure creation
     - Relationship storage

2. **API Layer (`api.py`)**
   - FastAPI-based REST endpoints
   - Task status monitoring
   - Search implementation
   - Response generation

3. **Database Layer (`db.py`)**
   - SingleStore connection management
   - Query execution and optimization
   - Vector and full-text search implementation

### Frontend Components

1. **Next.js Application**
   - Modern React-based interface
   - TypeScript for type safety
   - Tailwind CSS for styling

2. **Upload Interface**
   - Drag-and-drop file upload
   - Progress tracking
   - Status visualization
   - Error handling

3. **Search Interface**
   - Real-time query handling
   - Result visualization
   - Error handling and loading states

### Database Schema

The system uses five main tables in SingleStore:

1. **Document_Embeddings**
   - Document chunks and vector embeddings
   - HNSW vector index for similarity search
   - Full-text search capabilities

2. **Documents**
   - Document metadata
   - Parent table for document chunks

3. **Entities**
   - Extracted entities with properties
   - Optimized for distributed architecture

4. **Relationships**
   - Entity relationships
   - Source document links
   - Hash indexes for quick lookups

5. **ProcessingStatus**
   - Document processing status
   - Progress tracking
   - Error messages

## Technical Details

### Document Processing Pipeline

The system uses a sophisticated document processing pipeline:

1. **Semantic Chunking**
   - Gemini AI-powered chunking with structure preservation
   - Maintains document hierarchy and relationships
   - Preserves section headers with content
   - Special handling for feature lists and technical specifications

2. **Search and Retrieval**
   - Hybrid search combining vector and full-text matching
   - Vector similarity using OpenAI embeddings
   - TF-IDF based text search
   - Entity and relationship enrichment
   - Weighted scoring system

3. **Response Generation**
   - Context-aware prompt construction
   - Entity relationship integration
   - Structured output with citations
   - Confidence scoring

## Development Notes and Lessons Learned

### Frontend Component Architecture

1. **Graph Component Sizing**
   - When using react-force-graph-2d, proper container sizing is crucial
   - Always wrap the graph component in a parent div with fixed height
   - Use h-full on the graph component to fill parent container
   - Example structure:
     ```tsx
     // Parent component
     <section className="bg-white rounded-lg p-6 shadow-md">
       <h2>Knowledge Graph</h2>
       <div className="h-[500px]">
         <KnowledgeGraph />
       </div>
     </section>

     // KnowledgeGraph component
     <div className="relative w-full h-full">
       <ForceGraph2D {...props} />
     </div>
     ```
   - This prevents graph overflow and ensures proper containment

## Usage

### Document Processing

1. **Upload a Document**
   - Visit `http://localhost:3000/kb/upload`
   - Drag and drop a PDF file or click to browse
   - Monitor processing progress in real-time
   - View status updates for each processing stage

2. **View Knowledge Base**
   - After processing completes, you'll be redirected to the knowledge base
   - View processed documents and their statistics
   - Explore extracted entities and relationships

### Search Interface

1. Open `http://localhost:3000` in your browser
2. Enter your search query
3. View results including:
   - Relevant document chunks
   - Similarity scores
   - Extracted entities
   - Generated response

## API Documentation

Access the interactive API documentation at `http://localhost:8000/docs`

### Key Endpoints

- `POST /kag-search`: Search documents using natural language queries
  - Parameters:
    - `query`: Search query string
    - `top_k`: Number of results (default: 5)
    - `debug`: Enable debug mode (default: false)

- `POST /upload-pdf`: Upload and process a PDF file
  - Returns a task ID for tracking progress

- `GET /task-status/{task_id}`: Get processing status
  - Returns current status, progress, and any error messages

- `GET /kbdata`: Retrieve knowledge base statistics

## Troubleshooting

### Common Issues

1. **Connection Issues**
   - Verify SingleStore credentials in `.env`
   - Check Redis connection for task queue
   - Ensure all services are running (Redis, Celery, FastAPI)

2. **Processing Errors**
   - Check Celery worker logs for detailed error messages
   - Verify PDF file is not password protected
   - Ensure file size is under 50MB

3. **Performance Issues**
   - Monitor Redis memory usage
   - Check SingleStore query performance
   - Verify system resources (CPU, memory)

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Environment Variables

Required environment variables in `.env`:

```env
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
SINGLESTORE_HOST=your_db_host
SINGLESTORE_PORT=your_db_port
SINGLESTORE_USER=your_db_user
SINGLESTORE_PASSWORD=your_db_password
SINGLESTORE_DATABASE=your_db_name
REDIS_URL=redis://localhost:6379/0
```

## Development

- Backend uses FastAPI with Pydantic models
- Frontend uses Next.js 14 with TypeScript
- Database uses SingleStore with HNSW vector index
- API documentation available at http://localhost:8000/docs

## Development Status

### Completed Features
- [x] Document processing pipeline
- [x] Vector embeddings and storage
- [x] Knowledge graph generation
- [x] Hybrid search implementation
- [x] FastAPI backend
- [x] Next.js frontend
- [x] Basic error handling and logging

### Planned Enhancements
- [ ] Authentication system
- [ ] Rate limiting
- [ ] Batch document processing
- [ ] Advanced visualization
- [ ] Query caching
- [ ] Enhanced entity resolution
