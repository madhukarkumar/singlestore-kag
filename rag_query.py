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
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from db import DatabaseConnection
from models import Entity, Relationship, SearchResult, SearchResponse
from config_loader import config
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
            debug_output: If True, enable debug output mode
        """
        # Load environment variables
        load_dotenv(override=True)
        
        # Set up OpenAI client
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.openai_client = OpenAI()  # OpenAI will automatically use the OPENAI_API_KEY environment variable
        
        # Get configuration
        self.search_config = config.retrieval['search']
        self.response_config = config.retrieval['response_generation']
        
        # Debug configuration
        self.debug_output = debug_output
        self.debug_dir = "debug_output"
        if self.debug_output:
            os.makedirs(self.debug_dir, exist_ok=True)

    def get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for the query text."""
        try:
            response = self.openai_client.embeddings.create(
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
            # Extract key phrases (quoted terms)
            key_phrases = re.findall(r'"([^"]*)"', query)
            remaining_text = re.sub(r'"[^"]*"', '', query)
            
            # Split remaining text into terms
            terms = [t.strip() for t in remaining_text.split() if t.strip()]
            
            # Build search expression with semantic operators
            search_parts = []
            
            # Add exact phrases with high weight
            for phrase in key_phrases:
                if phrase:
                    search_parts.append(f'content:"\\"{phrase}\\"">>{self.search_config["exact_phrase_weight"]}')
            
            # Add individual terms with proximity search
            if terms:
                # Group terms with proximity operator
                terms_str = ' '.join(terms)
                search_parts.append(f'content:"{terms_str}"~{self.search_config["proximity_distance"]}')
                
                # Add individual terms with lower weight
                for term in terms:
                    if len(term) > 2:  # Skip very short terms
                        search_parts.append(f'content:"{term}">>{self.search_config["single_term_weight"]}')
            
            # Combine all parts
            formatted_query = ' '.join(search_parts)
            
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
        vector_weight: float = None
    ) -> List[Dict]:
        """Merge and rank results from vector and text searches."""
        # Use vector_weight from config if not provided
        if vector_weight is None:
            vector_weight = self.search_config["vector_weight"]
        
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

    def preprocess_query(self, query: str) -> str:
        """
        Preprocess the query to improve search accuracy:
        1. Remove special characters but keep important punctuation
        2. Normalize whitespace
        3. Extract key concepts and expand with synonyms
        """
        # Clean and normalize
        query = re.sub(r'[^\w\s?.!,]', ' ', query)
        query = ' '.join(query.split())
        
        # Extract key concepts using OpenAI
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system",
                    "content": "Extract and expand key concepts from the query. Format: concept1 | synonym1, synonym2 | concept2 | synonym1, synonym2"
                }, {
                    "role": "user",
                    "content": query
                }],
                temperature=0.0
            )
            
            # Parse expanded concepts
            expanded = response.choices[0].message.content
            expanded_terms = []
            for concept_group in expanded.split('|'):
                expanded_terms.extend(t.strip() for t in concept_group.split(','))
            
            # Combine original query with expanded terms
            enhanced_query = f"{query} {' '.join(expanded_terms)}"
            return enhanced_query.strip()
            
        except Exception as e:
            logger.warning(f"Query expansion failed: {str(e)}")
            return query

    def query(self, query_text: str, top_k: int = 5) -> SearchResponse:
        """Execute a hybrid search query combining vector and text search."""
        try:
            # Preprocess and enhance query
            enhanced_query = self.preprocess_query(query_text)
            logger.info(f"Enhanced query: {enhanced_query}")
            
            with DatabaseConnection() as db:
                # Get results from both search methods
                vector_results = self.vector_search(db, self.get_query_embedding(enhanced_query), limit=top_k)
                text_results = self.text_search(db, enhanced_query, limit=top_k)
                
                # Merge results
                merged_results = self.merge_search_results(vector_results, text_results)
                
                if self.debug_output:
                    self.save_debug_output("search_results", {
                        "query": query_text,
                        "results": merged_results
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

    def _build_prompt(self, query: str, context: Dict) -> str:
        """Build prompt for the LLM using retrieved context."""
        return config.get_response_prompt(query, context)
        
    def generate_response(self, query: str, context: Dict[str, Any]) -> str:
        """Generate a response using the LLM."""
        try:
            prompt = self._build_prompt(query, context)
            
            # Create API parameters
            api_params = {
                "model": self.response_config.get('model', 'o3-mini'),
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                    {"role": "user", "content": prompt}
                ]
            }
            
            # Add model-specific parameters
            if 'o3-' in api_params["model"]:
                api_params["max_completion_tokens"] = self.response_config['max_tokens']
            else:
                api_params["max_tokens"] = self.response_config['max_tokens']
                api_params["temperature"] = self.response_config['temperature']
            
            response = self.openai_client.chat.completions.create(**api_params)
            
            if not response.choices:
                logger.error("No response from OpenAI")
                return "I apologize, but I couldn't generate a response at this time."
                
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error while generating the response."

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
