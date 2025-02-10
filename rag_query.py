"""
RAG Query System for SingleStore Knowledge Graph.

This module implements a hybrid search system that combines:
1. Vector similarity search
2. Full-text search
3. Knowledge graph traversal
to answer natural language queries with citations.
"""

import os
import logging
import json
import time
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv
from db import DatabaseConnection
from models import Entity, Relationship, SearchResult, SearchResponse
import re
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class RAGQueryEngine:
    """Implements hybrid search combining vector similarity, text search, and knowledge graph."""
    
    def __init__(self, debug_output: bool = False):
        """
        Initialize the RAG Query Engine.
        
        Args:
            debug_output: If True, save intermediate results to JSON files
        """
        # Load environment variables
        load_dotenv(override=True)
        
        # Set up OpenAI client
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI()  # OpenAI will automatically use the OPENAI_API_KEY environment variable
        
        # Debug configuration
        self.debug_output = debug_output
        self.debug_dir = "debug_output"
        if debug_output:
            os.makedirs(self.debug_dir, exist_ok=True)

    def get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for the query text."""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=query
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting query embedding: {str(e)}")
            raise

    def vector_search(self, db: DatabaseConnection, query_embedding: List[float], limit: int = 10) -> List[Dict]:
        """Perform vector similarity search."""
        try:
            # Format vector for SQL
            vector_param = "[" + ",".join(f"{x:.6f}" for x in query_embedding) + "]"
            
            # Set vector parameter
            db.execute_query("SET @qvec = %s :> VECTOR(1536);", (vector_param,))
            
            # Execute search
            vector_search_sql = """
                SELECT doc_id, content, (embedding <*> @qvec) AS score
                FROM Document_Embeddings
                ORDER BY score DESC
                LIMIT %s;
            """
            # Log the SQL with actual parameter values for debugging
            debug_sql = vector_search_sql.replace("%s", str(limit))
            logger.info(f"Executing vector search SQL: {debug_sql}")
            logger.info(f"With parameters: limit={limit}")
            
            results = db.execute_query(vector_search_sql, (limit,))
            
            return [
                {"doc_id": r[0], "content": r[1], "score": r[2]}
                for r in results
            ]
        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            raise

    def text_search(self, db: DatabaseConnection, query: str, limit: int = 10) -> List[Dict]:
        """Perform full-text keyword search using Full-Text Search Version 2."""
        try:
            # Format query with content prefix and proper wrapping
            formatted_query = f'content:("{query}")'
            logger.info(f"Document_Embeddings table -> Formatted full-text search query: {formatted_query}")
            
            # Use the content_ft_idx full-text index
            sql = """
                SELECT 
                    doc_id,
                    content,
                    MATCH(TABLE Document_Embeddings) AGAINST(%s) as score
                FROM Document_Embeddings 
                WHERE MATCH(TABLE Document_Embeddings) AGAINST(%s)
                ORDER BY score DESC
                LIMIT %s;
            """
            # Log the SQL with actual parameter values for debugging
            debug_sql = sql.replace("%s", f"'{formatted_query}'", 2)  # Replace first two params
            debug_sql = debug_sql.replace("%s", str(limit))  # Replace limit param
            logger.info(f"Executing text search SQL: {debug_sql}")
            logger.info(f"With parameters: query={formatted_query}, limit={limit}")
            
            results = db.execute_query(sql, (formatted_query, formatted_query, limit))
            return [
                {
                    "doc_id": r[0],
                    "content": r[1],
                    "text_score": float(r[2])
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            return []

    def merge_search_results(
        self, 
        vector_results: List[Dict], 
        text_results: List[Dict],
        vector_weight: float = 0.7
    ) -> List[Dict]:
        """Merge and rank results from vector and text searches."""
        # Normalize scores
        vec_max = max([r["score"] for r in vector_results]) if vector_results else 1.0
        txt_max = max([r["text_score"] for r in text_results]) if text_results else 1.0
        
        # Merge results
        doc_scores = {}
        for doc in vector_results:
            doc_scores[doc["doc_id"]] = {
                "doc_id": doc["doc_id"],
                "content": doc["content"],
                "vector_score": doc["score"],
                "text_score": 0.0
            }
            
        for doc in text_results:
            if doc["doc_id"] in doc_scores:
                doc_scores[doc["doc_id"]]["text_score"] = doc["text_score"]
            else:
                doc_scores[doc["doc_id"]] = {
                    "doc_id": doc["doc_id"],
                    "content": doc["content"],
                    "vector_score": 0.0,
                    "text_score": doc["text_score"]
                }
        
        # Compute combined scores
        for doc in doc_scores.values():
            v_norm = (doc["vector_score"] / vec_max) if vec_max else 0.0
            t_norm = (doc["text_score"] / txt_max) if txt_max else 0.0
            doc["combined_score"] = vector_weight * v_norm + (1 - vector_weight) * t_norm
        
        return sorted(doc_scores.values(), key=lambda d: d["combined_score"], reverse=True)

    def get_entities_for_content(self, db: DatabaseConnection, content: str) -> List[Entity]:
        """Find entities mentioned in the content."""
        try:
            # Extract potential entity names using simple word-based approach
            # Remove special characters and split into words
            words = re.sub(r'[^\w\s]', ' ', content).split()
            # Get unique words, filter out common words and very short terms
            unique_terms = set(word.lower() for word in words if len(word) > 2)
            
            # Format terms for SQL query
            terms_str = ', '.join(f"'{term}'" for term in unique_terms)
            
            if not terms_str:
                return []
            
            # Query using schema-defined columns
            sql = """
                SELECT DISTINCT
                    entity_id,
                    name,
                    category,
                    COALESCE(description, '') as description,
                    COALESCE(aliases, '[]') as aliases
                FROM Entities
                WHERE LOWER(name) IN (%s)
                LIMIT 10;
            """ % terms_str
            
            logger.debug(f"Executing entity search SQL: {sql}")
            results = db.execute_query(sql)
            
            entities = []
            for r in results:
                try:
                    # Parse the JSON string into a Python list
                    aliases = json.loads(r[4]) if r[4] else []
                    
                    entity = Entity(
                        entity_id=r[0],  # Use entity_id to match the Field alias
                        name=r[1],
                        category=r[2],
                        description=r[3],
                        aliases=aliases
                    )
                    entities.append(entity)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse aliases JSON for entity {r[0]}: {e}")
                    # Continue with empty aliases if JSON parsing fails
                    entity = Entity(
                        entity_id=r[0],  # Use entity_id to match the Field alias
                        name=r[1],
                        category=r[2],
                        description=r[3],
                        aliases=[]
                    )
                    entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error finding entities: {str(e)}", exc_info=True)
            return []

    def get_relationships(self, db: DatabaseConnection, entity_ids: List[int]) -> List[Relationship]:
        """Get relationships for the given entities."""
        try:
            if not entity_ids:
                return []
            
            # Format entity IDs for SQL
            ids_str = ', '.join(str(id) for id in entity_ids)
            
            # Query using schema-defined columns
            sql = """
                SELECT DISTINCT
                    source_entity_id,
                    target_entity_id,
                    relation_type,
                    doc_id
                FROM Relationships
                WHERE source_entity_id IN (%s)
                OR target_entity_id IN (%s)
                LIMIT 20;
            """ % (ids_str, ids_str)
            
            results = db.execute_query(sql)
            
            return [
                Relationship(
                    source_entity_id=r[0],
                    target_entity_id=r[1],
                    relation_type=r[2],
                    metadata={"doc_id": r[3]} if r[3] else {}
                )
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting relationships: {str(e)}", exc_info=True)
            return []

    def generate_response(self, query: str, context: Dict) -> str:
        """Generate natural language response using OpenAI."""
        try:
            # Format context sections
            doc_section = "\n\n".join([
                f"Document {i+1}:\n"
                f"Content: {result.content}\n"
                f"Relevance Score: {result.combined_score:.3f}"
                for i, result in enumerate(context["results"])
            ])

            # Create a list of unique entities (using Entity's __hash__ and __eq__)
            all_entities = list({entity for result in context["results"] for entity in result.entities})

            entity_section = "\n".join([
                f"- {entity.name} (Type: {entity.category})"
                for entity in all_entities
            ])

            # Create a list of unique relationships
            all_relationships = list({
                (rel.source_entity_id, rel.target_entity_id, rel.relation_type)
                for result in context["results"]
                for rel in result.relationships
            })

            rel_section = "\n".join([
                f"- {rel_type}: Entity {src_id} -> Entity {tgt_id}"
                for src_id, tgt_id, rel_type in all_relationships
            ])

            # Build the prompt
            prompt = self._build_prompt(
                query=query,
                context={
                    "documents": doc_section,
                    "entities": entity_section,
                    "relationships": rel_section,
                    "query": query
                }
            )
            
            if self.debug_output:
                self.save_debug_output("formatted_prompt", {"prompt": prompt})
            
            # Call OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {
                        "role": "system", 
                        "content": """You are a knowledgeable assistant that provides accurate answers based on the given context. 
                        Follow these rules:
                        1. Only use information from the provided documents to answer the query
                        2. If the documents don't contain relevant information, say so
                        3. Make connections between entities and their relationships when relevant
                        4. Format your response with proper paragraphs and line breaks
                        5. Be concise but thorough"""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return f"I apologize, but I encountered an error while generating the response. Please try rephrasing your query or contact support if the issue persists."

    def _build_prompt(self, query: str, context: Dict) -> str:
        """Build prompt for the LLM using retrieved context."""
        try:
            with open('rag_prompt.md', 'r') as f:
                prompt_template = f.read()
            
            return prompt_template.format(
                documents=context["documents"],
                entities=context["entities"],
                relationships=context["relationships"],
                query=context["query"]
            )
        except Exception as e:
            logger.error(f"Error building prompt: {str(e)}")
            return ""

    def save_debug_output(self, stage: str, data: Dict) -> None:
        """Save intermediate results for debugging."""
        if not self.debug_output:
            return
            
        try:
            filename = f"rag_query_{stage}_{int(time.time())}.json"
            filepath = os.path.join(self.debug_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Debug output for {stage} saved to {filepath}")
            
        except Exception as e:
            logger.warning(f"Failed to save debug output: {str(e)}")

    def query(self, query_text: str, top_k: int = 5) -> SearchResponse:
        """Execute a hybrid search query combining vector and text search."""
        try:
            with DatabaseConnection() as db:
                # Get results from both search methods
                vector_results = self.vector_search(db, self.get_query_embedding(query_text), limit=top_k)
                text_results = self.text_search(db, query_text, limit=top_k)
                
                # Merge results
                merged_results = self.merge_search_results(
                    vector_results=vector_results,
                    text_results=text_results,
                    vector_weight=0.7
                )[:top_k]
                
                if self.debug_output:
                    self.save_debug_output("search_results", {
                        "query": query_text,
                        "vector_results": vector_results,
                        "text_results": text_results,
                        "merged_results": merged_results
                    })
                
                # Build context with SearchResult objects
                formatted_results = []
                for doc in merged_results:
                    # Get entities for this content
                    entities = self.get_entities_for_content(db, doc["content"])
                    
                    # Get relationships for these entities
                    relationships = self.get_relationships(db, [e.id for e in entities])
                    
                    # Create SearchResult object
                    search_result = SearchResult(
                        doc_id=doc["doc_id"],
                        content=doc["content"],
                        vector_score=doc.get("vector_score", 0.0),
                        text_score=doc.get("text_score", 0.0),
                        combined_score=doc["combined_score"],
                        entities=entities,
                        relationships=relationships
                    )
                    formatted_results.append(search_result)
                
                # Create SearchResponse
                response = SearchResponse(
                    query=query_text,
                    results=formatted_results,
                    generated_response=self.generate_response(query_text, {"results": formatted_results}),
                    execution_time=0.0  # We'll set this in the API layer
                )
                
                if self.debug_output:
                    self.save_debug_output("query_context", response.dict())
                
                return response
                
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}", exc_info=True)
            raise  # Let the API layer handle the error
