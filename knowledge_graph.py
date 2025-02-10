"""
Knowledge Graph Generator for SingleStore Document Processing.

This module extracts entities and relationships from document chunks using OpenAI's GPT models
and stores them in SingleStore for graph-based querying.
"""

import os
import json
import logging
from typing import Dict, List, Optional
import openai
from dotenv import load_dotenv
from db import DatabaseConnection
import time
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class KnowledgeGraphGenerator:
    """Generates knowledge graphs from document chunks using OpenAI."""
    
    def __init__(self, debug_output: bool = False):
        """
        Initialize the KnowledgeGraphGenerator with necessary configurations.
        
        Args:
            debug_output: If True, save extracted knowledge to local JSON files
        """
        # Load environment variables
        load_dotenv(override=True)
        
        # Set up OpenAI client
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        openai.api_key = self.openai_api_key
        self.client = openai
        
        # Debug configuration
        self.debug_output = debug_output
        self.debug_dir = "debug_output"
        if debug_output:
            os.makedirs(self.debug_dir, exist_ok=True)
        
        # Define the extraction prompt
        self.prompt_template = """You are a precise knowledge graph extraction system. Extract all entities and their relationships from the given text chunk.

Follow these rules strictly:
1. Identify ALL entities mentioned in the text (people, organizations, products, concepts, etc.)
2. Capture ALL relationships between these entities
3. Ensure high-quality entity descriptions
4. Include relevant aliases for entities
5. Assign appropriate categories to entities
6. Rate your confidence in each extraction (0.0 to 1.0)

Return ONLY a JSON object with this exact structure:
{{
    "entities": [
        {{
            "name": "string (required)",
            "description": "string (required)",
            "aliases": ["string"],
            "category": "string (required)",
            "confidence": float
        }}
    ],
    "relationships": [
        {{
            "source": "string (entity name)",
            "target": "string (entity name)",
            "relation_type": "string",
            "description": "string",
            "confidence": float,
            "doc_id": integer,
            "chunk_id": integer
        }}
    ]
}}

Text Chunk (ID: {chunk_id} from Document ID: {doc_id}):
\"\"\"
{text}
\"\"\"

Output only valid JSON, no other text:"""

    async def extract_knowledge(self, text: str, doc_id: int, chunk_id: int) -> Dict:
        """
        Extract entities and relationships from a text chunk using OpenAI.
        
        Args:
            text: The text chunk to analyze
            doc_id: Document identifier
            chunk_id: Chunk identifier within the document
            
        Returns:
            Dict containing entities and relationships
        """
        try:
            # Prepare the prompt
            prompt = self.prompt_template.format(
                text=text,
                doc_id=doc_id,
                chunk_id=chunk_id
            )
            
            # Call OpenAI API
            response = self.client.ChatCompletion.create(
                model="gpt-4-0125-preview",  # Using latest model for best extraction
                messages=[{"role": "user", "content": prompt}],
                temperature=0,  # Deterministic output
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            
            # Validate the response structure
            if not all(k in result for k in ["entities", "relationships"]):
                raise ValueError("Invalid response structure from OpenAI")
                
            return result
            
        except Exception as e:
            logger.error(f"Error extracting knowledge from chunk {chunk_id}: {str(e)}")
            raise
    
    def save_debug_output(self, data: Dict, doc_id: int, chunk_id: Optional[int] = None) -> None:
        """
        Save extracted knowledge to a JSON file for debugging.
        
        Args:
            data: Dictionary containing extracted knowledge
            doc_id: Document identifier
            chunk_id: Optional chunk identifier
        """
        if not self.debug_output:
            return
            
        try:
            # Create a filename based on doc_id and chunk_id
            filename = f"doc_{doc_id}"
            if chunk_id is not None:
                filename += f"_chunk_{chunk_id}"
            filename += f"_{int(time.time())}.json"
            
            filepath = os.path.join(self.debug_dir, filename)
            
            # Add metadata to the output
            debug_data = {
                "metadata": {
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "timestamp": datetime.datetime.now().isoformat(),
                },
                "extracted_data": data
            }
            
            # Save to file with pretty printing
            with open(filepath, 'w') as f:
                json.dump(debug_data, f, indent=2)
            
            logger.debug(f"Debug output saved to {filepath}")
            
        except Exception as e:
            logger.warning(f"Failed to save debug output: {str(e)}")
    
    async def store_knowledge(self, knowledge: Dict, db: DatabaseConnection) -> None:
        """
        Store extracted knowledge in SingleStore.
        
        Args:
            knowledge: Dict containing entities and relationships
            db: Database connection instance
        """
        try:
            # Store entities
            for entity in knowledge["entities"]:
                insert_entity_query = """
                INSERT INTO Entities (name, description, aliases, category)
                VALUES (%s, %s, %s, %s)
                """
                db.execute_query(
                    insert_entity_query,
                    (
                        entity["name"],
                        entity["description"],
                        json.dumps(entity.get("aliases", [])),
                        entity["category"]
                    )
                )
                
            # Store relationships
            for rel in knowledge["relationships"]:
                insert_rel_query = """
                INSERT INTO Relationships 
                (source_entity_id, target_entity_id, relation_type, doc_id)
                SELECT 
                    s.entity_id, 
                    t.entity_id, 
                    %s,
                    %s
                FROM Entities s
                JOIN Entities t
                WHERE s.name = %s AND t.name = %s
                """
                db.execute_query(
                    insert_rel_query,
                    (
                        rel["relation_type"],
                        rel["doc_id"],
                        rel["source"],
                        rel["target"]
                    )
                )
                
        except Exception as e:
            logger.error(f"Error storing knowledge in database: {str(e)}")
            raise
    
    async def process_document(self, doc_id: int) -> None:
        """
        Process all chunks from a document to extract and store knowledge.
        
        Args:
            doc_id: Document identifier to process
        """
        try:
            with DatabaseConnection() as db:
                # Get all chunks for the document
                query = """
                SELECT content, embedding_id 
                FROM Document_Embeddings 
                WHERE doc_id = %s
                """
                chunks = db.execute_query(query, (doc_id,))
                
                # Process each chunk
                for chunk in chunks:
                    chunk_text = chunk[0]
                    chunk_id = chunk[1]
                    
                    # Extract knowledge
                    logger.info(f"Processing chunk {chunk_id} from document {doc_id}")
                    knowledge = await self.extract_knowledge(chunk_text, doc_id, chunk_id)
                    
                    # Save debug output
                    self.save_debug_output(knowledge, doc_id, chunk_id)
                    
                    # Store knowledge
                    await self.store_knowledge(knowledge, db)
                    
                logger.info(f"Successfully processed document {doc_id}")
                
        except Exception as e:
            logger.error(f"Error processing document {doc_id}: {str(e)}")
            raise

async def main():
    """Command line interface for knowledge graph generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate knowledge graph from documents")
    parser.add_argument("--doc_id", type=int, required=True, help="Document ID to process")
    parser.add_argument("--debug", action="store_true", help="Enable debug output to JSON files")
    
    args = parser.parse_args()
    
    try:
        generator = KnowledgeGraphGenerator(debug_output=args.debug)
        await generator.process_document(args.doc_id)
        logger.info("Knowledge graph generation completed successfully")
        
    except Exception as e:
        logger.error(f"Knowledge graph generation failed: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
