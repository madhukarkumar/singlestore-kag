# SingleStore Knowledge Graph Search

A full-stack application that processes documents to create semantic embeddings and knowledge graphs using OpenAI and Google's Gemini AI models. The system uses SingleStore for storing and querying vector embeddings, document content, and knowledge graph relationships.

## Features

- **Document Processing**
  - PDF and Markdown document processing
  - Semantic chunking using Google's Gemini AI
  - Vector embeddings using OpenAI's text-embedding-ada-002
  - Automatic knowledge graph generation

- **Search Capabilities**
  - Hybrid search combining vector similarity and full-text search
  - Entity and relationship extraction
  - Natural language response generation
  - Fast and accurate document retrieval

- **Modern Web Interface**
  - Clean and responsive Next.js frontend
  - Real-time search results
  - Detailed result display with scores and entities
  - Mobile-friendly design

## System Architecture

### Backend Components

1. **Document Processing (`main.py`)**
   - Handles PDF to markdown conversion
   - Creates semantic chunks using Gemini AI
   - Generates embeddings using OpenAI

2. **Knowledge Graph Generation (`knowledge_graph.py`)**
   - Extracts entities and relationships
   - Creates graph structure
   - Stores relationships in SingleStore

3. **Search API (`api.py`)**
   - FastAPI-based REST endpoints
   - Hybrid search implementation
   - Response generation using OpenAI

4. **Database Layer (`db.py`)**
   - SingleStore connection management
   - Query execution and optimization
   - Vector and full-text search implementation

### Frontend Components

1. **Next.js Application**
   - Modern React-based interface
   - TypeScript for type safety
   - Tailwind CSS for styling

2. **Search Interface**
   - Real-time query handling
   - Result visualization
   - Error handling and loading states

### Database Schema

The system uses four main tables in SingleStore:

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

## Setup and Installation

### Prerequisites

- Python 3.12.9
- Node.js 18+ and pnpm
- SingleStore database
- OpenAI API key
- Google Gemini API key

### Backend Setup

1. **Python Environment Setup**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
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
   ```

3. **Database Setup**
   ```bash
   # Connect to SingleStore and run schema
   mysql -h <host> -u <user> -p <database> < schema.sql
   ```

### Frontend Setup

1. **Install Dependencies**
   ```bash
   cd frontend
   pnpm install
   ```

2. **Environment Configuration**
   The frontend is pre-configured to connect to the backend at `http://localhost:8000`.

## Running the Application

1. **Start the Backend Server**
   ```bash
   # From the project root
   uvicorn api:app --reload
   ```
   The API will be available at `http://localhost:8000`

2. **Start the Frontend Development Server**
   ```bash
   # In a new terminal, from the frontend directory
   cd frontend
   pnpm dev
   ```
   The web interface will be available at `http://localhost:3000`

## Usage

### Processing Documents

1. **Add a New Document**
   ```bash
   python main.py path/to/document.pdf --document_id 1
   ```
   This will:
   - Convert PDF to markdown with semantic chunks
   - Generate embeddings
   - Store in SingleStore

2. **Generate Knowledge Graph**
   ```bash
   python knowledge_graph.py --doc_id 1
   ```

### Using the Search Interface

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

- `POST /kag-search`
  - Search documents using natural language queries
  - Parameters:
    - `query`: Search query string
    - `top_k`: Number of results (default: 5)
    - `debug`: Enable debug mode (default: false)

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

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
