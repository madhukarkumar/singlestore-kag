from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging
import os
from typing import List, Dict, Optional
from rag_query import RAGQueryEngine
from db import DatabaseConnection
import time
from models import SearchRequest, SearchResponse, SearchResult, Entity, Relationship

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
