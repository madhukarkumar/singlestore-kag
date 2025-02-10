from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging
import os
from typing import List, Dict, Optional
from rag_query import RAGQueryEngine
from db import DatabaseConnection
import time
from models import SearchRequest, SearchResponse, SearchResult, Entity, Relationship, KBDataResponse, KBStats, DocumentStats
from datetime import datetime

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
        db.close()
        logger.info("Database connection closed")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # NextJS default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
