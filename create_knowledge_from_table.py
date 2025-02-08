#!/usr/bin/env python3
import os
import json
import sys
import logging
import openai
from db import DatabaseConnection

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Set your OpenAI API key from the environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.error("Please set the OPENAI_API_KEY environment variable.")
    sys.exit(1)

def extract_triples(text_chunk):
    """
    Sends the provided text_chunk to a reasoning LLM (via OpenAI)
    with instructions to extract knowledge as triples.
    
    Returns:
        A list of triples (each triple is a dict with keys:
        "subject", "predicate", "object", and "properties").
    """
    prompt = f"""
You are an expert in extracting structured knowledge from text. 
Given the following text, extract the knowledge as triples (subject, predicate, object) along with any additional properties.

Instructions:
- Identify key entities mentioned in the text as subjects and objects.
- Identify the relationship between them as the predicate.
- For each triple, output in the following JSON format:

{{
  "triples": [
    {{
      "subject": "Entity name or ID for the subject",
      "predicate": "Relationship type",
      "object": "Entity name or ID for the object",
      "properties": {{}}
    }}
  ]
}}

Text:
{text_chunk}

Return only the JSON output.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or any suitable reasoning model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500
        )
        response_content = response.choices[0].message.content.strip()

        # Attempt to parse the returned JSON.
        data = json.loads(response_content)
        return data.get("triples", [])
    except Exception as e:
        logger.error("Error extracting triples from text chunk: %s", str(e))
        return []

def get_or_create_entity(db: DatabaseConnection, entity_data: dict) -> int:
    """Get existing entity ID or create new entity."""
    try:
        # Check if entity exists
        select_query = """
            SELECT entity_id 
            FROM Entities 
            WHERE name = %s 
            LIMIT 1
        """
        result = db.execute_query(select_query, (entity_data['name'],))
        
        if result:
            return result[0][0]
        
        # Create new entity
        insert_query = """
            INSERT INTO Entities 
            (name, description, aliases, category)
            VALUES (%s, %s, %s, %s)
        """
        db.execute_query(
            insert_query,
            (
                entity_data['name'],
                entity_data.get('description'),
                json.dumps(entity_data.get('aliases', [])),
                entity_data.get('category')
            )
        )
        
        # Get the new entity_id
        result = db.execute_query("SELECT LAST_INSERT_ID()")
        return result[0][0]
        
    except Exception as e:
        logger.error("Failed to get/create entity: %s", str(e))
        raise

def main():
    try:
        # Use DatabaseConnection class with context manager
        with DatabaseConnection() as db:
            # Fetch all document embeddings
            rows = db.execute_query("""
                SELECT embedding_id, content, doc_id 
                FROM Document_Embeddings 
                ORDER BY doc_id, embedding_id
            """)
            
            if not rows:
                logger.info("No document embeddings found to process.")
                return
            
            for row in rows:
                embedding_id, text_chunk, doc_id = row
                
                logger.info("Processing document embedding ID: %d", doc_id)
                triples = extract_triples(text_chunk)
                logger.info("Extracted %d triple(s) from document ID: %d", len(triples), doc_id)

                for triple in triples:
                    subject_id = get_or_create_entity(db, {'name': triple.get("subject", "")})
                    object_id = get_or_create_entity(db, {'name': triple.get("object", "")})
                    
                    # Insert relationship
                    insert_relationship = """
                        INSERT INTO Relationships 
                        (source_entity_id, target_entity_id, relation_type, doc_id)
                        VALUES (%s, %s, %s, %s)
                    """
                    db.execute_query(
                        insert_relationship,
                        (subject_id, object_id, triple.get("predicate", ""), doc_id)
                    )
            
            logger.info("Processing complete.")

    except Exception as e:
        logger.error("Processing failed: %s", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
