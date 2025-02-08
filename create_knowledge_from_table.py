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

def main():
    try:
        # Use DatabaseConnection class with context manager
        with DatabaseConnection() as db:
            # Fetch all document embeddings
            rows = db.execute_query("SELECT id, text_chunk FROM document_embeddings")
            if not rows:
                logger.info("No document embeddings found to process.")
                return

            # Iterate over each document embedding
            for row in rows:
                doc_id = row[0]  # id is first column
                text_chunk = row[1]  # text_chunk is second column

                logger.info("Processing document embedding ID: %d", doc_id)
                triples = extract_triples(text_chunk)
                logger.info("Extracted %d triple(s) from document ID: %d", len(triples), doc_id)

                # Insert each extracted triple into the knowledge_graph table
                for triple in triples:
                    subject = triple.get("subject", "")
                    predicate = triple.get("predicate", "")
                    object_ = triple.get("object", "")
                    properties = triple.get("properties", {})

                    insert_query = """
                        INSERT INTO knowledge_graph (subject, predicate, object, properties)
                        VALUES (%s, %s, %s, %s)
                    """
                    try:
                        # Convert properties to JSON string
                        db.execute_query(
                            insert_query, 
                            (subject, predicate, object_, json.dumps(properties))
                        )
                    except Exception as e:
                        logger.error("Error inserting triple for document ID %d: %s", doc_id, str(e))
                        raise

        logger.info("Processing complete.")

    except Exception as e:
        logger.error("Processing failed: %s", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
