"""
RAG Query System for SingleStore Knowledge Graph.

This module implements a hybrid search system that combines:
1. Vector similarity search
2. Full-text search
3. Knowledge graph traversal
to answer natural language queries with citations.
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
import openai
from dotenv import load_dotenv
from db import DatabaseConnection
import re

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
        self.client = openai.OpenAI()
        
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

    def get_entities_for_content(self, db: DatabaseConnection, content: str) -> List[Dict]:
        """Find entities mentioned in the content."""
        try:
            # Extract potential entity names using simple word-based approach
            # Remove special characters and split into words
            words = re.sub(r'[^\w\s]', ' ', content).split()
            # Get unique words, filter out common words and very short terms
            unique_terms = set(word.lower() for word in words if len(word) > 2)
            # Convert to a SQL-safe list format
            search_terms = ' '.join(unique_terms)
            
            # Limit the search terms to prevent overwhelming the query
            if len(search_terms) > 1000:  # Reasonable limit for search terms
                search_terms = search_terms[:1000]
            
            # Format query with name prefix and proper wrapping
            formatted_query = f'name:("{search_terms}")'
            logger.info(f"Entities table -> Formatted full-text search query: {formatted_query}")
            
            query = """
                SELECT DISTINCT
                    entity_id,
                    name,
                    category,
                    description
                FROM Entities
                WHERE MATCH(TABLE Entities) AGAINST(%s)
                   OR LOWER(name) LIKE CONCAT('%%', LOWER(%s), '%%')
                LIMIT 10;
            """
            # Log the SQL with actual parameter values for debugging
            debug_sql = query.replace("%s", f"'{formatted_query}'")  # Replace first param
            debug_sql = debug_sql.replace("%s", f"'{search_terms}'")  # Replace second param
            logger.info(f"Executing entity search SQL: {debug_sql}")
            logger.info(f"With search terms: {formatted_query}")
            
            # For LIKE clause, use original search terms without prefix
            results = db.execute_query(query, (formatted_query, search_terms))
            return [
                {
                    "id": r[0],
                    "name": r[1],
                    "type": r[2],
                    "description": r[3]
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Error finding entities: {str(e)}")
            return []

    def get_relationships(self, db: DatabaseConnection, entity_ids: List[int]) -> List[Dict]:
        """Get relationships for the given entities."""
        try:
            if not entity_ids:
                return []
                
            placeholders = ','.join(['%s'] * len(entity_ids))
            query = f"""
                SELECT DISTINCT
                    r.relationship_id,
                    r.source_entity_id,
                    se.name as source_name,
                    r.target_entity_id,
                    te.name as target_name,
                    r.relation_type
                FROM Relationships r
                JOIN Entities se ON r.source_entity_id = se.entity_id
                JOIN Entities te ON r.target_entity_id = te.entity_id
                WHERE r.source_entity_id IN ({placeholders})
                   OR r.target_entity_id IN ({placeholders})
                LIMIT 50;
            """
            # Log the SQL with actual parameter values for debugging
            debug_sql = query.replace(placeholders, str(entity_ids))
            logger.info(f"Executing relationship search SQL: {debug_sql}")
            logger.info(f"With entity IDs: {entity_ids}")
            
            # Need to pass entity_ids twice since we use the list in both IN clauses
            results = db.execute_query(query, entity_ids + entity_ids)
            return [
                {
                    "id": r[0],
                    "source_id": r[1],
                    "source_name": r[2],
                    "target_id": r[3],
                    "target_name": r[4],
                    "relation_type": r[5]
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Error finding relationships: {str(e)}")
            return []

    def generate_response(self, query: str, context: Dict) -> str:
        """Generate natural language response using OpenAI."""
        try:
            # Load and format the prompt template
            with open('rag_prompt.md', 'r') as f:
                prompt_template = f.read()
            
            # Build document section
            doc_lines = []
            for doc in context.get("documents", []):
                content = doc["content"].strip().replace("\n", " ")
                doc_lines.append(f'Document: "{content}"')
            doc_section = "\n".join(doc_lines)
            
            # Build entity section
            entity_lines = []
            for entity in context.get("entities", []):
                entity_lines.append(
                    f"- {entity['name']} ({entity.get('category', 'Unknown')}): {entity.get('description', '')}"
                )
            entity_section = "\n".join(entity_lines)
            
            # Build relationship section
            rel_lines = []
            for rel in context.get("relationships", []):
                rel_lines.append(
                    f"- {rel.get('source_name', '')} —({rel.get('relation_type', '')})→ {rel.get('target_name', '')}"
                )
            rel_section = "\n".join(rel_lines)
            
            # Format the complete prompt
            prompt = prompt_template.format(
                documents=doc_section,
                entities=entity_section,
                relationships=rel_section,
                query=query
            )
            
            if self.debug_output:
                self.save_debug_output("formatted_prompt", {"prompt": prompt})
            
            # Call OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a knowledgeable assistant that provides accurate answers based on the given context. Make connections between entities and their relationships to provide comprehensive answers."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"Error generating response: {str(e)}"

    def _build_prompt(self, query: str, context: Dict) -> str:
        """Build prompt for the LLM using retrieved context."""
        try:
            with open('rag_prompt.md', 'r') as f:
                prompt_template = f.read()
            
            return prompt_template.format(
                documents=context["documents"],
                entities=context["entities"],
                relationships=context["relationships"],
                query=query
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

    def query(self, query_text: str, top_k: int = 5) -> str:
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
                
                # Extract entities and relationships
                context = {
                    "documents": [
                        {
                            "doc_id": doc["doc_id"],
                            "content": doc["content"],
                            "score": doc["combined_score"]
                        }
                        for doc in merged_results
                    ],
                    "entities": [],
                    "relationships": []
                }
                
                all_entities = []
                for doc in merged_results:
                    entities = self.get_entities_for_content(db, doc["content"])
                    all_entities.extend(entities)
                
                # Remove duplicates
                unique_entities = {e["id"]: e for e in all_entities}.values()
                context["entities"] = list(unique_entities)
                
                entity_ids = [e["id"] for e in unique_entities]
                relationships = self.get_relationships(db, entity_ids)
                context["relationships"] = relationships
                
                if self.debug_output:
                    self.save_debug_output("query_context", context)
                
                # Generate response
                return self.generate_response(query_text, context)
                
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise

def main():
    """Command line interface for RAG queries."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Query the knowledge base using RAG")
    parser.add_argument("query", help="Natural language query to process")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--top_k", type=int, default=5, help="Number of top results to consider")
    
    args = parser.parse_args()
    
    try:
        engine = RAGQueryEngine(debug_output=args.debug)
        response = engine.query(args.query, top_k=args.top_k)
        print("\nResponse:")
        print("-" * 80)
        print(response)
        print("-" * 80)
        
    except Exception as e:
        logger.error(f"Query processing failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
