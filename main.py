import os
import sys
import argparse
import logging
import json
import numpy as np
from db import DatabaseConnection

import requests
import openai
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import google.generativeai as genai

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv(override=True)  # Add override=True to force reload

# Environment keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")

if not GEMINI_API_KEY or not OPENAI_API_KEY or not PROJECT_ID:
    print("DEBUG: Environment variables:")
    print(f"GEMINI_API_KEY present: {bool(GEMINI_API_KEY)}")
    print(f"GEMINI_API_KEY value ends with: {GEMINI_API_KEY[-8:] if GEMINI_API_KEY else 'None'}")
    print(f"OPENAI_API_KEY present: {bool(OPENAI_API_KEY)}")
    print(f"PROJECT_ID present: {bool(PROJECT_ID)}")
    logging.error("API keys or PROJECT_ID are missing in the .env file.")
    sys.exit(1)

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY


def get_chunks(pdf_path: str) -> str:
    """
    OCR the pdf file into Markdown. Tables should be formatted as HTML. Do not surround your output with triple backticks.
    Chunk the document into sections of roughly 250 - 1000 words. Our goal is to identify parts of the page with same semantic theme.
    Annotate the chunks in the final respnse between <chunk> </chunk>markers. These chunks will be embedded and used in a RAG pipeline
    
    :param pdf_path: Path to the pdf file.
    :return: Path to the generated markdown file.
    """
    print("DEBUG: Starting processing of PDF file:", pdf_path)
    logging.info("Reading PDF file: %s", pdf_path)
    
    try:
        reader = PdfReader(pdf_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text()
    except Exception as e:
        logging.error("Error reading PDF: %s", str(e))
        raise

    print("DEBUG: Configuring GenAI with API key")
    # Mask the API key for security while debugging
    masked_key = GEMINI_API_KEY[-8:] if GEMINI_API_KEY else None
    print(f"DEBUG: Using API key ending in: {masked_key}")
    genai.configure(api_key=GEMINI_API_KEY)

    try:
        print("DEBUG: Preparing content for generation")
        prompt = """OCR the following document into Markdown. Tables should be formatted as HTML. Do not surround your output with triple backticks. Chunk the document into sections of roughly 250 - 1000 words. Our goal is to identify parts of the page with same semantic theme. Annotate the chunks in the final respnse between <chunk> </chunk>markers. These chunks will be embedded and used in a RAG pipeline.

Document text:
"""
        content = prompt + full_text
        
        print("DEBUG: Calling GenAI generate_content")
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(content)
        print("DEBUG: Received response from GenAI")

        if not response or not hasattr(response, 'text'):
            raise ValueError("Invalid response from GenAI SDK")

        # The response is already in markdown format with semantic chunks
        md_content = response.text
        
        # Determine markdown file path (same folder as PDF, same name as pdf but with .md extension)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        md_path = os.path.join(os.path.dirname(pdf_path), f"{base_name}.md")
        
        print(f"DEBUG: Writing markdown content to {md_path}")
        try:
            with open(md_path, "w", encoding="utf-8") as md_file:
                md_file.write(md_content)
            logging.info("Markdown file written: %s", md_path)
        except Exception as e:
            logging.error("Error writing markdown file: %s", str(e))
            raise

        return md_path

    except Exception as err:
        print("DEBUG: An error occurred in GenAI SDK call:", err)
        logging.error("Processing failed: %s", err)
        raise


def create_embeddings(markdown_path: str, embedding_model: str = EMBEDDING_MODEL):
    """
    Read the markdown file containing semantic chunks and create embeddings using OpenAI embedding model.
    Store the embeddings in a text file in the same folder as the markdown file.
    
    :param markdown_path: Path to the markdown file.
    :param embedding_model: Embedding model to use.
    :return: Path to the embeddings file.
    """
    print("DEBUG: Starting embedding creation for file:", markdown_path)
    logging.info("Reading markdown file: %s", markdown_path)
    
    try:
        with open(markdown_path, "r", encoding="utf-8") as f:
            md_text = f.read()
    except Exception as e:
        logging.error("Error reading markdown file: %s", str(e))
        raise

    # Split the markdown content into chunks using the <chunk> markers
    chunks = []
    for chunk in md_text.split("<chunk>"):
        if chunk.strip():
            # Remove the closing tag if present and strip whitespace
            chunk = chunk.replace("</chunk>", "").strip()
            if chunk:
                chunks.append(chunk)

    print(f"DEBUG: Found {len(chunks)} chunks to process")
    
    try:
        # Create embeddings for each chunk using new OpenAI API syntax
        print("DEBUG: Creating embeddings using OpenAI API")
        client = openai.OpenAI()  # Initialize the client
        embeddings = []
        
        for i, chunk in enumerate(chunks):
            print(f"DEBUG: Processing chunk {i+1}/{len(chunks)}")
            response = client.embeddings.create(
                model=embedding_model,
                input=chunk
            )
            embedding = response.data[0].embedding
            embeddings.append({
                'chunk': chunk,
                'embedding': embedding
            })
            print(f"DEBUG: Created embedding for chunk {i+1}, vector size: {len(embedding)}")

        # Create the output file path
        base_name = os.path.splitext(markdown_path)[0]
        embeddings_path = f"{base_name}_embeddings.txt"
        
        # Write embeddings to file
        print(f"DEBUG: Writing embeddings to {embeddings_path}")
        with open(embeddings_path, "w", encoding="utf-8") as f:
            json.dump(embeddings, f, indent=2)
        
        print(f"DEBUG: Successfully wrote embeddings for {len(chunks)} chunks")
        logging.info("Embeddings file written: %s", embeddings_path)
        
        return embeddings_path

    except Exception as err:
        print("DEBUG: An error occurred while creating embeddings:", err)
        logging.error("Embedding creation failed: %s", err)
        raise


def insert_embeddings_to_db(embeddings_file: str, document_id: int) -> None:
    """
    Insert text chunks and their embeddings into SingleStore database.
    
    :param embeddings_file: Path to the JSON file containing chunks and embeddings
    :param document_id: Unique identifier for the document these embeddings belong to
    """
    logger.info("Inserting embeddings from file: %s", embeddings_file)
    
    try:
        # Read the embeddings file
        with open(embeddings_file, 'r') as f:
            data = json.load(f)
        
        # Connect to database
        db = DatabaseConnection()
        db.connect()
        
        # Prepare insert query
        insert_query = """
            INSERT INTO document_embeddings 
            (text_chunk, vector, document_id)
            VALUES (%s, %s, %s)
        """
        
        # Insert each chunk and its embedding
        for item in data:
            chunk = item['chunk']
            embedding = np.array(item['embedding'], dtype=np.float32)
            
            try:
                db.cursor.execute(insert_query, (chunk, embedding.tobytes(), document_id))
                db.conn.commit()
            except Exception as e:
                logger.error("Error inserting chunk: %s", str(e))
                db.conn.rollback()
                raise
        
        logger.info("Successfully inserted %d chunks for document_id %d", len(data), document_id)
        
    except Exception as e:
        logger.error("Failed to insert embeddings: %s", str(e))
        raise
    finally:
        if db and db.conn:
            db.close()


def main():
    parser = argparse.ArgumentParser(description="Process PDF documents and create embeddings")
    parser.add_argument("--pdf", type=str, help="Path to the PDF file to process")
    parser.add_argument("--markdown", type=str, help="Path to an existing markdown file to process")
    parser.add_argument("--embeddings", type=str, help="Path to an existing embeddings file to insert into database")
    parser.add_argument("--document_id", type=int, help="Document ID for database insertion", default=None)
    
    args = parser.parse_args()
    
    try:
        if args.embeddings and args.document_id is not None:
            # Insert existing embeddings into database
            insert_embeddings_to_db(args.embeddings, args.document_id)
            return
            
        if args.pdf:
            # Process PDF file
            md_path = get_chunks(args.pdf)
        elif args.markdown:
            # Use existing markdown file
            md_path = args.markdown
        else:
            parser.error("Either --pdf or --markdown must be specified")
            
        # Create embeddings
        embeddings_path = create_embeddings(md_path)
        
        # If document_id is provided, also insert into database
        if args.document_id is not None:
            insert_embeddings_to_db(embeddings_path, args.document_id)
            
    except Exception as e:
        logger.error("Processing failed: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
