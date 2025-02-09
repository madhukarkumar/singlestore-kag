from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging
import os
from typing import List, Dict
from rag_query import RAGQueryEngine
from db import DatabaseConnection
import time

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str

class SearchResult(BaseModel):
    doc_id: int
    content: str
    vector_score: float = 0.0
    text_score: float = 0.0
    combined_score: float = 0.0
    entities: List[Dict] = []

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    execution_time: float

@app.post("/kag-search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Endpoint for document search using natural language queries
    """
    try:
        # Initialize RAG Query Engine
        rag_engine = RAGQueryEngine()
        
        # Get query embedding
        start_time = time.time()
        query_embedding = rag_engine.get_query_embedding(request.query)
        
        # Perform searches
        vector_results = rag_engine.vector_search(db, query_embedding)
        text_results = rag_engine.text_search(db, request.query)
        
        # Merge results
        merged_results = rag_engine.merge_search_results(vector_results, text_results)
        
        # Get entities for each result
        formatted_results = []
        for result in merged_results:
            entities = rag_engine.get_entities_for_content(db, result["content"])
            search_result = SearchResult(
                doc_id=result["doc_id"],
                content=result["content"],
                vector_score=result.get("vector_score", 0.0),
                text_score=result.get("text_score", 0.0),
                combined_score=result["combined_score"],
                entities=entities
            )
            formatted_results.append(search_result)
        
        execution_time = time.time() - start_time
        
        return SearchResponse(
            query=request.query,
            results=formatted_results,
            execution_time=execution_time
        )
    
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
