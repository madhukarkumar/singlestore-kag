from fastapi import FastAPI, HTTPException, Query, File, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging
import os
from typing import List, Dict, Optional, Union
from rag_query import RAGQueryEngine
from db import DatabaseConnection
import time
from models import SearchRequest, SearchResponse, SearchResult, Entity, Relationship, KBDataResponse, KBStats, DocumentStats, GraphResponse, GraphData, GraphNode, GraphLink, ProcessingStatusResponse
from datetime import datetime
from pdf_processor import save_pdf, create_document_record, get_processing_status, cleanup_processing, PDFProcessingError
from tasks import process_pdf_task
from celery.result import AsyncResult

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(override=True)

app = FastAPI(title="KagSearch API",
             description="API for document search functionality",
             version="0.1.0")

# Database connection
db = None

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    global db
    try:
        db = DatabaseConnection()
        db.connect()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    global db
    if db:
        db.disconnect()
        logger.info("Database connection closed")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskResponse(BaseModel):
    """Response model for task status"""
    task_id: str
    doc_id: int
    status: str
    message: Optional[str] = None

# In-memory status cache
processing_status_cache: Dict[int, ProcessingStatusResponse] = {}

async def update_status_cache(doc_id: int, status: ProcessingStatusResponse):
    """Update the in-memory status cache"""
    processing_status_cache[doc_id] = status

@app.get("/processing-status/{doc_id}", response_model=ProcessingStatusResponse)
async def get_status(doc_id: int):
    """Get current processing status"""
    try:
        # First check the cache
        if doc_id in processing_status_cache:
            return processing_status_cache[doc_id]
            
        # If not in cache, get from database
        logger.info(f"Getting processing status for doc_id: {doc_id}")
        try:
            status = get_processing_status(doc_id)
            # Update cache
            await update_status_cache(doc_id, status)
            return status
        except Exception as e:
            # If database query fails, return last known status from cache
            if doc_id in processing_status_cache:
                return processing_status_cache[doc_id]
            raise
            
    except ValueError as e:
        logger.error(f"Processing status not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-pdf", status_code=status.HTTP_202_ACCEPTED, response_model=TaskResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file"""
    try:
        # Save the uploaded file
        logger.info(f"Saving uploaded file: {file.filename}")
        file_content = await file.read()
        file_path = save_pdf(file_content, file.filename)
        
        # Create document record
        doc_id = create_document_record(file.filename, str(file_path), len(file_content))
        logger.info(f"Created document record with ID: {doc_id}")
        
        # Initialize status in cache
        await update_status_cache(doc_id, ProcessingStatusResponse(
            currentStep="started",
            fileName=file.filename
        ))
        
        # Start celery task
        task = process_pdf_task.delay(doc_id)
        logger.info(f"Started Celery task {task.id} for doc_id {doc_id}")
        
        return TaskResponse(
            task_id=task.id,
            doc_id=doc_id,
            status="pending",
            message="Processing started"
        )
        
    except PDFProcessingError as e:
        logger.error(f"PDF processing error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a Celery task"""
    try:
        task = AsyncResult(task_id)
        
        # Get task state and info
        state = task.state
        info = task.info or {}
        
        # Build response based on state
        response = {
            "task_id": task_id,
            "status": state,
            "message": info.get('status', ''),
            "current": info.get('current', 0),
            "total": info.get('total', 100)
        }
        
        # Add error info if failed
        if state == "FAILURE":
            response["error"] = str(task.result)
            
        return response
        
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting task status: {str(e)}"
        )

@app.post("/kag-search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Endpoint for document search using natural language queries
    """
    try:
        # Initialize RAG Query Engine and start timing
        start_time = time.time()
        rag_engine = RAGQueryEngine(debug_output=request.debug)
        
        # Execute query
        response = rag_engine.query(
            query_text=request.query,
            top_k=request.top_k
        )
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Create SearchResponse
        search_response = SearchResponse(
            query=request.query,
            results=response.results,  
            generated_response=response.generated_response,
            execution_time=execution_time
        )
        
        return search_response
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/kbdata", response_model=KBDataResponse)
async def get_kb_data():
    """Get knowledge base statistics and document information."""
    start_time = time.time()
    try:
        with DatabaseConnection() as conn:
            # Get total counts
            total_docs = conn.execute_query("SELECT COUNT(*) FROM Documents")[0][0]
            total_chunks = conn.execute_query("SELECT COUNT(*) FROM Document_Embeddings")[0][0]
            total_entities = conn.execute_query("SELECT COUNT(*) FROM Entities")[0][0]
            total_relationships = conn.execute_query("SELECT COUNT(*) FROM Relationships")[0][0]

            # Get document details
            doc_query = """
                SELECT 
                    d.doc_id,
                    COALESCE(d.title, 'Untitled') as title,
                    COALESCE(d.publish_date, CURRENT_DATE()) as created_at,
                    'document' as file_type,
                    'processed' as status,
                    COUNT(DISTINCT de.embedding_id) as chunk_count,
                    COUNT(DISTINCT e.entity_id) as entity_count,
                    COUNT(DISTINCT r.relationship_id) as relationship_count
                FROM Documents d
                LEFT JOIN Document_Embeddings de ON d.doc_id = de.doc_id
                LEFT JOIN Relationships r ON r.doc_id = d.doc_id
                LEFT JOIN Entities e ON (
                    e.entity_id = r.source_entity_id OR 
                    e.entity_id = r.target_entity_id
                )
                GROUP BY d.doc_id, d.title, d.publish_date
                ORDER BY d.publish_date DESC NULLS LAST
            """
            docs = conn.execute_query(doc_query)

            # Format document stats
            doc_stats = []
            for doc in docs:
                created_at = doc[2].isoformat() if doc[2] else datetime.now().isoformat()
                doc_stats.append(
                    DocumentStats(
                        doc_id=doc[0],
                        title=doc[1],
                        total_chunks=doc[5],
                        total_entities=doc[6],
                        total_relationships=doc[7],
                        created_at=created_at,
                        file_type=doc[3],
                        status=doc[4]
                    )
                )

            # Create response
            kb_stats = KBStats(
                total_documents=total_docs,
                total_chunks=total_chunks,
                total_entities=total_entities,
                total_relationships=total_relationships,
                documents=doc_stats,
                last_updated=datetime.now().isoformat()
            )

            return KBDataResponse(
                stats=kb_stats,
                execution_time=time.time() - start_time
            )

    except Exception as e:
        logger.error(f"Error getting KB stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving knowledge base data: {str(e)}"
        )

@app.get("/graph-data", response_model=GraphResponse)
async def get_graph_data():
    """Get knowledge graph visualization data."""
    start_time = time.time()
    try:
        with DatabaseConnection() as conn:
            # Get unique categories and assign group numbers
            category_query = """
                SELECT DISTINCT category 
                FROM Entities 
                WHERE category IS NOT NULL
                ORDER BY category
            """
            categories = conn.execute_query(category_query)
            category_to_group = {cat[0]: idx for idx, cat in enumerate(categories, 1)}
            
            # Get all entities
            entity_query = """
                SELECT 
                    entity_id,
                    name,
                    COALESCE(category, 'unknown') as category,
                    COUNT(DISTINCT r1.relationship_id) + COUNT(DISTINCT r2.relationship_id) as connection_count
                FROM Entities e
                LEFT JOIN Relationships r1 ON e.entity_id = r1.source_entity_id
                LEFT JOIN Relationships r2 ON e.entity_id = r2.target_entity_id
                GROUP BY entity_id, name, category
            """
            entities = conn.execute_query(entity_query)
            
            # Get all relationships
            relationship_query = """
                SELECT 
                    r.source_entity_id,
                    r.target_entity_id,
                    r.relation_type,
                    COUNT(*) as weight
                FROM Relationships r
                GROUP BY source_entity_id, target_entity_id, relation_type
            """
            relationships = conn.execute_query(relationship_query)
            
            # Create nodes
            nodes = [
                GraphNode(
                    id=str(entity[0]),
                    name=entity[1],
                    category=entity[2],
                    group=category_to_group.get(entity[2], 0),
                    val=max(1, int(entity[3]))  # Node size based on connections
                )
                for entity in entities
            ]
            
            # Create links
            links = [
                GraphLink(
                    source=str(rel[0]),
                    target=str(rel[1]),
                    type=rel[2],
                    value=int(rel[3])  # Link thickness based on relationship count
                )
                for rel in relationships
            ]
            
            return GraphResponse(
                data=GraphData(nodes=nodes, links=links),
                execution_time=time.time() - start_time
            )

    except Exception as e:
        logger.error(f"Error getting graph data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving graph data: {str(e)}"
        )

@app.delete("/cancel-processing/{doc_id}")
async def cancel_processing(doc_id: int):
    try:
        cleanup_processing(doc_id)
        return {"status": "cancelled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
