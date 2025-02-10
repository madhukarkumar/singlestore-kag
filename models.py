"""Shared Pydantic models for the SingleStore Knowledge Graph Search application."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

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
