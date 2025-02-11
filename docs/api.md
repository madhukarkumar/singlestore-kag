# KagSearch API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, the API does not require authentication. CORS is configured to allow requests from `http://localhost:3000`.

## Endpoints

### Document Processing

#### Upload PDF
```http
POST /upload-pdf
Content-Type: multipart/form-data
```

Upload and process a PDF file. The file will be processed asynchronously.

**Request Body:**
- `file`: PDF file (max size: 50MB)

**Response:**
```json
{
  "task_id": "string",
  "doc_id": "integer",
  "status": "string",
  "message": "string"
}
```

**Status Codes:**
- `202 Accepted`: File accepted for processing
- `400 Bad Request`: Invalid file or format
- `500 Internal Server Error`: Server error

#### Get Task Status
```http
GET /task-status/{task_id}
```

Get the current status of a processing task.

**Parameters:**
- `task_id`: Task ID returned from upload-pdf endpoint

**Response:**
```json
{
  "task_id": "string",
  "status": "string",
  "message": "string",
  "current": "integer",
  "total": "integer",
  "error": "string (optional)"
}
```

**Status Values:**
- `PENDING`: Task is waiting to be processed
- `STARTED`: Task has started
- `PROCESSING`: Task is in progress
- `SUCCESS`: Task completed successfully
- `FAILURE`: Task failed

**Status Codes:**
- `200 OK`: Status retrieved successfully
- `404 Not Found`: Task not found
- `500 Internal Server Error`: Server error

#### Get Processing Status
```http
GET /processing-status/{doc_id}
```

Get detailed processing status for a document.

**Parameters:**
- `doc_id`: Document ID

**Response:**
```json
{
  "currentStep": "string",
  "errorMessage": "string (optional)",
  "fileName": "string"
}
```

**Status Codes:**
- `200 OK`: Status retrieved successfully
- `404 Not Found`: Document not found
- `500 Internal Server Error`: Server error

### Search

#### Search Documents
```http
POST /kag-search
Content-Type: application/json
```

Search documents using natural language queries.

**Request Body:**
```json
{
  "query": "string",
  "top_k": "integer (optional, default: 5)",
  "debug": "boolean (optional, default: false)"
}
```

**Response:**
```json
{
  "query": "string",
  "results": [
    {
      "content": "string",
      "score": "float",
      "doc_id": "integer",
      "entities": [
        {
          "name": "string",
          "description": "string",
          "category": "string"
        }
      ],
      "relationships": [
        {
          "source": "string",
          "target": "string",
          "relation_type": "string"
        }
      ]
    }
  ],
  "generated_response": "string",
  "execution_time": "float"
}
```

**Status Codes:**
- `200 OK`: Search completed successfully
- `400 Bad Request`: Invalid query parameters
- `500 Internal Server Error`: Server error

### Knowledge Base

#### Get Knowledge Base Data
```http
GET /kbdata
```

Get statistics and information about the knowledge base.

**Response:**
```json
{
  "total_documents": "integer",
  "total_chunks": "integer",
  "total_entities": "integer",
  "total_relationships": "integer",
  "document_stats": [
    {
      "doc_id": "integer",
      "title": "string",
      "chunk_count": "integer",
      "entity_count": "integer",
      "relationship_count": "integer"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Data retrieved successfully
- `500 Internal Server Error`: Server error

#### Get Graph Data
```http
GET /graph-data
```

Get knowledge graph visualization data.

**Response:**
```json
{
  "nodes": [
    {
      "id": "string",
      "name": "string",
      "category": "string",
      "value": "integer"
    }
  ],
  "links": [
    {
      "source": "string",
      "target": "string",
      "value": "integer",
      "relation_type": "string"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Data retrieved successfully
- `500 Internal Server Error`: Server error

### Management

#### Cancel Processing
```http
POST /cancel-processing/{doc_id}
```

Cancel document processing and clean up resources.

**Parameters:**
- `doc_id`: Document ID to cancel

**Response:**
```json
{
  "message": "string",
  "doc_id": "integer"
}
```

**Status Codes:**
- `200 OK`: Processing cancelled successfully
- `404 Not Found`: Document not found
- `500 Internal Server Error`: Server error

## Error Handling

All endpoints may return error responses in the following format:
```json
{
  "detail": "string"
}
```

Common error status codes:
- `400 Bad Request`: Invalid request parameters or data
- `404 Not Found`: Requested resource not found
- `500 Internal Server Error`: Server-side error

## Rate Limiting
Currently, there are no rate limits implemented.

## Best Practices

1. **File Upload:**
   - Keep file sizes under 50MB
   - Use PDF format only
   - Avoid password-protected files

2. **Task Status Polling:**
   - Poll task status every 2 seconds
   - Stop polling on terminal states (SUCCESS, FAILURE)
   - Handle timeouts (5 minutes max processing time)

3. **Search Queries:**
   - Use natural language queries
   - Keep queries concise and specific
   - Use the debug flag for detailed search information

4. **Error Handling:**
   - Always check response status codes
   - Handle error responses appropriately
   - Implement proper retry logic for failed requests
