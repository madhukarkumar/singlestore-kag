from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging
import os
from typing import List, Dict, Optional
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
    allow_origins=["http://localhost:3000"],  # NextJS default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    debug: Optional[bool] = False

class Entity(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None

class Relationship(BaseModel):
    source_id: int
    target_id: int
    relationship_type: str
    metadata: Optional[Dict] = None

class SearchResult(BaseModel):
    doc_id: int
    content: str
    vector_score: float = 0.0
    text_score: float = 0.0
    combined_score: float = 0.0
    entities: List[Entity] = []
    relationships: List[Relationship] = []

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    generated_response: Optional[str] = None
    execution_time: float

@app.post("/kag-search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Endpoint for document search using natural language queries
    """
    try:
        # Initialize RAG Query Engine and start timing
        start_time = time.time()
        rag_engine = RAGQueryEngine(debug_output=request.debug)
        
        # Get query embedding
        query_embedding = rag_engine.get_query_embedding(request.query)
        
        # Perform searches
        vector_results = rag_engine.vector_search(db, query_embedding, limit=request.top_k)
        text_results = rag_engine.text_search(db, request.query, limit=request.top_k)
        
        # Merge results
        merged_results = rag_engine.merge_search_results(vector_results, text_results)
        
        # Get entities and relationships for each result
        formatted_results = []
        all_entities = []
        
        for result in merged_results:
            # Get entities for this content
            entities = rag_engine.get_entities_for_content(db, result["content"])
            all_entities.extend(entities)
            
            # Create search result
            search_result = SearchResult(
                doc_id=result["doc_id"],
                content=result["content"],
                vector_score=result.get("vector_score", 0.0),
                text_score=result.get("text_score", 0.0),
                combined_score=result["combined_score"],
                entities=[Entity(**e) for e in entities],
                relationships=[]  # Will be populated below
            )
            formatted_results.append(search_result)
        
        # Get relationships for all entities
        if all_entities:
            entity_ids = list({e["id"] for e in all_entities})  # Get unique entity IDs
            relationships = rag_engine.get_relationships(db, entity_ids)
            
            # Add relationships to results where entities match
            for result in formatted_results:
                result_entity_ids = {e.id for e in result.entities}
                result.relationships = [
                    Relationship(**r) for r in relationships
                    if r["source_id"] in result_entity_ids or r["target_id"] in result_entity_ids
                ]
        
        # Generate response using context
        context = {
            "results": formatted_results,
            "entities": [Entity(**e) for e in all_entities],
            "query": request.query
        }
        generated_response = rag_engine.generate_response(request.query, context)
        
        execution_time = time.time() - start_time
        
        return SearchResponse(
            query=request.query,
            results=formatted_results,
            generated_response=generated_response,
            execution_time=execution_time
        )
    
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
