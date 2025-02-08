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

class DocumentProcessor:
    """A class to handle document processing, embedding creation, and database operations."""
    
    def __init__(self):
        """Initialize the DocumentProcessor with necessary configurations."""
        # Load environment variables
        load_dotenv(override=True)
        
        # Set up API keys and configurations
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.project_id = os.getenv("PROJECT_ID")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
        
        # Validate environment variables
        self._validate_env_vars()
        
        # Configure APIs
        openai.api_key = self.openai_api_key
        genai.configure(api_key=self.gemini_api_key)
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI()
        
        # Initialize Gemini model
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
    
    def _validate_env_vars(self):
        """Validate that all required environment variables are set."""
        if not self.gemini_api_key or not self.openai_api_key or not self.project_id:
            logger.debug("Environment variables:")
            logger.debug(f"GEMINI_API_KEY present: {bool(self.gemini_api_key)}")
            logger.debug(f"GEMINI_API_KEY value ends with: {self.gemini_api_key[-8:] if self.gemini_api_key else 'None'}")
            logger.debug(f"OPENAI_API_KEY present: {bool(self.openai_api_key)}")
            logger.debug(f"PROJECT_ID present: {bool(self.project_id)}")
            raise ValueError("API keys or PROJECT_ID are missing in the .env file.")

    def get_chunks(self, pdf_path: str) -> str:
        """
        Process a PDF file into markdown with semantic chunks.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            str: Path to the generated markdown file.
        """
        logger.info("Reading PDF file: %s", pdf_path)
        
        try:
            # Read PDF content
            reader = PdfReader(pdf_path)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text()
                
            # Prepare prompt for Gemini
            prompt = """OCR the following document into Markdown. Tables should be formatted as HTML. 
            Do not surround your output with triple backticks. Chunk the document into sections of 
            roughly 250 - 1000 words. Our goal is to identify parts of the page with same semantic theme. 
            Annotate the chunks in the final response between <chunk> </chunk>markers. These chunks will 
            be embedded and used in a RAG pipeline.

            Document text:
            """
            content = prompt + full_text
            
            # Generate chunks using Gemini
            logger.debug("Calling Gemini generate_content")
            response = self.gemini_model.generate_content(content)
            
            if not response or not hasattr(response, 'text'):
                raise ValueError("Invalid response from GenAI SDK")
            
            # Save markdown content
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            md_path = os.path.join(os.path.dirname(pdf_path), f"{base_name}.md")
            
            with open(md_path, "w", encoding="utf-8") as md_file:
                md_file.write(response.text)
                
            logger.info("Markdown file written: %s", md_path)
            return md_path
            
        except Exception as e:
            logger.error("Error processing PDF: %s", str(e))
            raise

    def create_embeddings(self, input_markdown_file, output_json_file):
        """
        Create embeddings from markdown chunks and save to JSON.
        
        Args:
            input_markdown_file: Path to markdown file with <chunk> tags
            output_json_file: Path to save embeddings JSON
            
        Returns:
            None
        """
        # Read the markdown file content
        try:
            with open(input_markdown_file, 'r', encoding='utf-8') as f:
                markdown_text = f.read()
        except Exception as e:
            logging.error(f"Failed to read input file {input_markdown_file}: {e}")
            return

        # Extract chunks marked with <chunk> tags
        chunks = []
        import re
        chunk_pattern = r'<chunk>(.*?)</chunk>'
        chunks = re.findall(chunk_pattern, markdown_text, re.DOTALL)
        
        if not chunks:
            logger.warning("No chunks found with <chunk> tags. Using whole text as single chunk.")
            chunks = [markdown_text]

        embeddings_data = []
        for idx, chunk in enumerate(chunks):
            # Skip empty chunks if any
            chunk = chunk.strip()
            if not chunk or chunk.isspace():
                continue
                
            try:
                # Generate embedding using the OpenAI client (1.0.0+ syntax)
                response = self.openai_client.embeddings.create(
                    input=chunk,
                    model=self.embedding_model
                )
                embedding_vector = response.data[0].embedding  # list of floats
            except Exception as e:
                logging.error(f"Embedding generation failed for chunk {idx}: {e}")
                continue

            # Convert to float32 numpy array for SingleStore compatibility
            embedding_array = np.array(embedding_vector, dtype=np.float32)
            # Verify the embedding has correct dimensions
            expected_dims = 3072 if self.embedding_model == "text-embedding-3-large" else 1536
            if embedding_array.shape[0] != expected_dims:
                logging.error(
                    f"Embedding dimension mismatch for chunk {idx}: "
                    f"expected {expected_dims}, got {embedding_array.shape[0]}"
                )
                continue

            # Convert numpy array back to list for JSON serialization
            embedding_list = embedding_array.tolist()
            # Preserve original JSON structure in the record
            record = {
                "chunk_index": idx,
                "text": chunk,
                "embedding": embedding_list
            }
            embeddings_data.append(record)

        # Save the list of embedding records to a JSON file
        try:
            with open(output_json_file, 'w', encoding='utf-8') as out_f:
                json.dump(embeddings_data, out_f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(embeddings_data)} embeddings to {output_json_file}")
        except Exception as e:
            logging.error(f"Failed to write embeddings to {output_json_file}: {e}")

    def insert_embeddings_to_db(self, embeddings_file: str, document_id: int) -> None:
        """
        Insert embeddings into SingleStore database.
        
        Args:
            embeddings_file: Path to the JSON file containing chunks and embeddings.
            document_id: Unique identifier for the document.
        """
        try:
            # Load embeddings from JSON file
            with open(embeddings_file, 'r') as f:
                data = json.load(f)
                
            logger.info("Inserting embeddings from file: %s", embeddings_file)
            
            # Connect to database
            with DatabaseConnection() as db:
                logger.info("Successfully connected to SingleStore database")
                
                # Create table if not exists
                insert_query = """
                INSERT INTO document_embeddings 
                (document_id, chunk_text, embedding) 
                VALUES (%s, %s, %s)
                """
                
                logger.debug("Using insert query template: %s", insert_query)
                
                for item in data:
                    chunk = item['text']
                    embedding = np.array(item['embedding'], dtype=np.float32)
                    embedding_bytes = embedding.tobytes()
                    
                    # Log query details for debugging
                    debug_query = insert_query % (
                        document_id,
                        repr(chunk[:50] + "..." if len(chunk) > 50 else chunk),
                        f"BINARY({len(embedding_bytes)} bytes)"
                    )
                    logger.debug("Executing query: %s", debug_query)
                    
                    db.execute_query(insert_query, (document_id, chunk, embedding_bytes))
                
                logger.info("Successfully inserted %d chunks for document_id %d", len(data), document_id)
        
        except Exception as e:
            logger.error("Failed to insert embeddings: %s", str(e))
            raise

    def process_document(self, input_path: str, document_id: int) -> dict:
        """
        Process a document end-to-end: create chunks, embeddings, and insert into database.
        
        Args:
            input_path: Path to the input file (PDF or markdown).
            document_id: Unique identifier for the document.
            
        Returns:
            dict: Processing results including file paths and statistics.
        """
        try:
            results = {
                'input_path': input_path,
                'document_id': document_id,
                'markdown_path': None,
                'embeddings_path': None,
                'chunks_count': 0
            }
            
            # Process PDF if needed
            if input_path.endswith('.pdf'):
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                md_path = os.path.join(os.path.dirname(input_path), f"{base_name}.md")
                
                # If markdown exists, use it; otherwise process PDF
                if os.path.exists(md_path):
                    logger.info("Using existing markdown file: %s", md_path)
                    results['markdown_path'] = md_path
                else:
                    results['markdown_path'] = self.get_chunks(input_path)
            else:
                results['markdown_path'] = input_path
            
            # Create embeddings
            embeddings_path = f"{os.path.splitext(results['markdown_path'])[0]}_embeddings.json"
            results['embeddings_path'] = embeddings_path
            self.create_embeddings(results['markdown_path'], embeddings_path)
            
            # Insert into database
            self.insert_embeddings_to_db(results['embeddings_path'], document_id)
            
            # Get chunks count
            with open(results['embeddings_path'], 'r') as f:
                results['chunks_count'] = len(json.load(f))
            
            return results
            
        except Exception as e:
            logger.error("Document processing failed: %s", str(e))
            raise

def main():
    """Main entry point for the document processing pipeline."""
    parser = argparse.ArgumentParser(description="Process documents and create embeddings")
    parser.add_argument("input_file", help="Path to the input document (PDF or markdown)")
    parser.add_argument("--document_id", type=int, required=True, help="Unique identifier for the document")
    parser.add_argument("--chunks_only", action="store_true", help="Only create chunks, don't generate embeddings")
    parser.add_argument("--store_embeddings", action="store_true", help="Store existing embeddings from JSON file into SingleStore")
    
    args = parser.parse_args()
    
    try:
        processor = DocumentProcessor()
        
        if args.store_embeddings:
            # Assume embeddings file exists with .json extension
            embeddings_file = f"{os.path.splitext(args.input_file)[0]}_embeddings.json"
            if not os.path.exists(embeddings_file):
                logger.error(f"Embeddings file not found: {embeddings_file}")
                sys.exit(1)
            processor.insert_embeddings_to_db(embeddings_file, args.document_id)
            logger.info("Successfully stored embeddings in SingleStore")
            return
        
        # Normal processing flow
        if args.chunks_only:
            # Only create chunks, don't generate embeddings or store in DB
            if args.input_file.endswith('.pdf'):
                md_path = processor.get_chunks(args.input_file)
                logger.info("Created chunks in markdown file: %s", md_path)
            else:
                logger.info("Input is already markdown, no chunk creation needed")
            return
        
        # Full processing with embeddings and DB storage
        output_file = processor.process_document(
            args.input_file,
            args.document_id,
        )
        logger.info("Processing completed. Output file: %s", output_file)
        
    except Exception as e:
        logger.error("Processing failed: %s", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
