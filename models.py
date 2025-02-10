"""Shared Pydantic models for the SingleStore Knowledge Graph Search application."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Entity(BaseModel):
    """Entity model representing items in the knowledge graph."""
    id: int = Field(alias="entity_id")
    name: str
    category: str
    description: Optional[str] = None
    aliases: Optional[List[str]] = []

    def __hash__(self):
        return hash((self.id, self.name))

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.id == other.id and self.name == other.name

class Relationship(BaseModel):
    """Relationship model representing connections between entities."""
    source_entity_id: int
    target_entity_id: int
    relation_type: str
    metadata: Optional[Dict] = {}

class SearchResult(BaseModel):
    """Search result model containing document content and metadata."""
    doc_id: int
    content: str
    vector_score: float = 0.0
    text_score: float = 0.0
    combined_score: float = 0.0
    entities: List[Entity] = []
    relationships: List[Relationship] = []

class SearchRequest(BaseModel):
    """Search request parameters."""
    query: str
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    debug: Optional[bool] = False

class SearchResponse(BaseModel):
    """Search response containing results and metadata."""
    query: str
    results: List[SearchResult]
    generated_response: Optional[str] = None
    execution_time: float

class DocumentStats(BaseModel):
    """Statistics for a document in the knowledge base."""
    doc_id: int
    title: str
    total_chunks: int
    total_entities: int
    total_relationships: int
    created_at: str
    file_type: str
    status: str = "processed"

class KBStats(BaseModel):
    """Overall knowledge base statistics."""
    total_documents: int
    total_chunks: int
    total_entities: int
    total_relationships: int
    documents: List[DocumentStats]
    last_updated: str

class KBDataResponse(BaseModel):
    """Response model for KB statistics endpoint."""
    stats: KBStats
    execution_time: float

class GraphNode(BaseModel):
    """Node in the knowledge graph visualization."""
    id: str
    name: str
    category: str
    group: int  # For coloring by category
    val: int = 1  # For node size

class GraphLink(BaseModel):
    """Link/relationship in the knowledge graph visualization."""
    source: str
    target: str
    type: str
    value: int = 1  # For link thickness

class GraphData(BaseModel):
    """Complete graph data for visualization."""
    nodes: List[GraphNode]
    links: List[GraphLink]

class GraphResponse(BaseModel):
    """Response model for graph data endpoint."""
    data: GraphData
    execution_time: float

class ProcessingStatus(BaseModel):
    doc_id: int
    file_name: str
    file_path: str
    file_size: int
    current_step: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ProcessingStatusResponse(BaseModel):
    currentStep: str
    errorMessage: Optional[str] = None
    fileName: str
