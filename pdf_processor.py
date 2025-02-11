import os
import fitz  # PyMuPDF
from datetime import datetime
from typing import Optional, Tuple, List
from pathlib import Path
from db import DatabaseConnection
from models import ProcessingStatus, ProcessingStatusResponse
import logging
import json
from knowledge_graph import KnowledgeGraphGenerator
from openai import OpenAI
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

# Set up logging
logger = logging.getLogger(__name__)

DOCUMENTS_DIR = Path("documents")
DOCUMENTS_DIR.mkdir(exist_ok=True)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

class PDFProcessingError(Exception):
    pass

def validate_pdf(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate PDF file for size and password protection.
    Returns (is_valid, error_message)
    """
    try:
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:  # 50MB
            return False, "File size exceeds 50MB limit"

        doc = fitz.open(file_path)
        if doc.needs_pass:
            doc.close()
            return False, "Password-protected PDFs are not supported"
            
        doc.close()
        return True, None
    except Exception as e:
        return False, f"Invalid PDF file: {str(e)}"

def save_pdf(file_data: bytes, filename: str) -> str:
    """Save PDF file to documents directory"""
    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
    file_path = DOCUMENTS_DIR / safe_filename
    
    # Check if file exists
    if file_path.exists():
        raise PDFProcessingError("A file with this name already exists")
    
    with open(file_path, "wb") as f:
        f.write(file_data)
    
    return str(file_path)

def create_document_record(filename: str, file_path: str, file_size: int) -> int:
    """Create initial document record and return doc_id"""
    conn = DatabaseConnection()
    try:
        conn.connect()
        logger.info(f"Creating document record for {filename}")
        
        # Create document record
        query = """
            INSERT INTO Documents (title, source)
            VALUES (%s, %s)
        """
        conn.execute_query(query, (filename, file_path))
        logger.info("Document record created")
        
        # Get the last inserted ID
        doc_id = conn.execute_query("SELECT LAST_INSERT_ID()")[0][0]
        logger.info(f"Got document ID: {doc_id}")
        
        # Create processing status record
        query = """
            INSERT INTO ProcessingStatus 
            (doc_id, file_name, file_path, file_size, current_step)
            VALUES (%s, %s, %s, %s, 'started')
        """
        conn.execute_query(query, (doc_id, filename, file_path, file_size))
        logger.info("Processing status record created")
        
        return doc_id
    except Exception as e:
        logger.error(f"Error creating document record: {str(e)}", exc_info=True)
        raise
    finally:
        conn.disconnect()

def update_processing_status(doc_id: int, step: str, error_message: Optional[str] = None):
    """Update processing status for a document"""
    conn = DatabaseConnection()
    try:
        conn.connect()
        query = """
            UPDATE ProcessingStatus 
            SET current_step = %s,
                error_message = %s,
                updated_at = NOW()
            WHERE doc_id = %s
        """
        conn.execute_query(query, (step, error_message, doc_id))
    finally:
        conn.disconnect()

def get_processing_status(doc_id: int) -> ProcessingStatusResponse:
    """Get current processing status"""
    conn = DatabaseConnection()
    try:
        conn.connect()
        query = """
            SELECT current_step, error_message, file_name, 
                   TIMESTAMPDIFF(SECOND, last_updated, NOW()) as seconds_since_update
            FROM ProcessingStatus
            WHERE doc_id = %s
        """
        result = conn.execute_query(query, (doc_id,))
        if not result:
            raise ValueError(f"No processing status found for doc_id {doc_id}")
            
        current_step, error_message, file_name, seconds_since_update = result[0]
        
        # If the operation is taking too long (over 5 minutes), mark it as failed
        if seconds_since_update > 300 and current_step not in ['completed', 'failed']:
            error_message = "Operation timed out after 5 minutes"
            update_processing_status(doc_id, 'failed', error_message)
            current_step = 'failed'
            
        return ProcessingStatusResponse(
            currentStep=current_step,
            errorMessage=error_message,
            fileName=file_name
        )
    finally:
        conn.disconnect()

def cleanup_processing(doc_id: int):
    """Clean up processing data for cancelled/failed jobs"""
    conn = DatabaseConnection()
    try:
        conn.connect()
        # Delete document record
        conn.execute_query("DELETE FROM Documents WHERE doc_id = %s", (doc_id,))
        # Delete processing status
        conn.execute_query("DELETE FROM ProcessingStatus WHERE doc_id = %s", (doc_id,))
        # Delete any chunks
        conn.execute_query("DELETE FROM Document_Embeddings WHERE doc_id = %s", (doc_id,))
    finally:
        conn.disconnect()

def get_semantic_chunks(text: str) -> List[str]:
    """Use Gemini to get semantic chunks from text."""
    try:
        prompt = f"""Split the following text into semantic chunks. Each chunk should be a coherent unit of information.
        Keep related concepts together, especially for lists and feature descriptions.
        Return only the chunks, one per line, with '---' as separator.
        
        Text to split:
        {text}
        """
        
        logger.info("Sending request to Gemini for semantic chunking")
        logger.info(f"Input text length: {len(text)} characters")
        logger.info(f"Input text preview: {text[:200]}...")
        
        response = model.generate_content(prompt)
        logger.info("Received response from Gemini")
        
        if not response.text:
            logger.warning("Gemini returned empty response, falling back to basic chunking")
            return [text]
            
        logger.info(f"Raw Gemini response: {response.text}")
            
        # Split response into chunks
        chunks = [chunk.strip() for chunk in response.text.split('---') if chunk.strip()]
        
        if not chunks:
            logger.warning("No valid chunks found in Gemini response, falling back to basic chunking")
            return [text]
            
        # Log each chunk
        logger.info(f"Generated {len(chunks)} semantic chunks:")
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Chunk {i}/{len(chunks)}:")
            logger.info(f"Length: {len(chunk)} characters")
            logger.info(f"Content: {chunk}")
            logger.info("-" * 80)
            
        return chunks
        
    except Exception as e:
        logger.error(f"Error in semantic chunking: {str(e)}")
        logger.warning("Falling back to basic chunking")
        return [text]

def process_pdf(doc_id: int, task=None):
    """Process PDF file through all steps"""
    conn = DatabaseConnection()
    client = OpenAI()
    try:
        conn.connect()
        logger.info(f"Starting PDF processing for doc_id: {doc_id}")
        
        # Get document info
        query = "SELECT title, source FROM Documents WHERE doc_id = %s"
        result = conn.execute_query(query, (doc_id,))
        if not result:
            raise ValueError(f"Document not found: {doc_id}")
            
        filename, file_path = result[0]
        logger.info(f"Found document: {filename} at {file_path}")
        
        # Update status to chunking
        update_processing_status(doc_id, "chunking")
        if task:
            task.update_state(state='PROCESSING', meta={
                'status': 'Validating and chunking PDF...',
                'current': 10,
                'total': 100
            })
        
        # Validate PDF
        logger.info("Validating PDF...")
        is_valid, error = validate_pdf(file_path)
        if not is_valid:
            logger.error(f"PDF validation failed: {error}")
            raise PDFProcessingError(error)
            
        # Extract text
        logger.info("Starting text extraction...")
        doc = fitz.open(file_path)
        
        # Process each page
        total_pages = len(doc)
        logger.info(f"Processing {total_pages} pages...")
        
        for page_num in range(total_pages):
            logger.info(f"Processing page {page_num + 1}/{total_pages}")
            page = doc[page_num]
            text = page.get_text()
            
            if text.strip():
                # Get semantic chunks using Gemini
                logger.info(f"Getting semantic chunks for page {page_num + 1}")
                semantic_chunks = get_semantic_chunks(text)
                
                for chunk in semantic_chunks:
                    if not chunk.strip():
                        continue
                        
                    try:
                        logger.info(f"Generating embedding for chunk (size: {len(chunk)})")
                        response = client.embeddings.create(
                            input=chunk,
                            model="text-embedding-ada-002"
                        )
                        embedding = response.data[0].embedding
                        
                        # Store text and embedding
                        query = """
                            INSERT INTO Document_Embeddings 
                            (doc_id, content, embedding)
                            VALUES (%s, %s, JSON_ARRAY_PACK(%s))
                        """
                        conn.execute_query(query, (doc_id, chunk, json.dumps(embedding)))
                        logger.info(f"Stored chunk and embedding successfully")
                    except Exception as e:
                        logger.error(f"Error processing chunk: {str(e)}")
                        raise PDFProcessingError(f"Failed to process chunk: {str(e)}")
            
            if task:
                # Update progress (40% of total progress allocated to PDF processing)
                progress = 10 + int((page_num + 1) / total_pages * 40)
                task.update_state(state='PROCESSING', meta={
                    'status': f'Processing page {page_num + 1} of {total_pages}',
                    'current': progress,
                    'total': 100
                })
        
        doc.close()
        logger.info("PDF processing completed successfully")
        
        # Generate knowledge graph
        logger.info("Starting knowledge graph generation...")
        update_processing_status(doc_id, "entities")
        if task:
            task.update_state(state='PROCESSING', meta={
                'status': 'Generating knowledge graph...',
                'current': 50,
                'total': 100
            })
        
        kg_generator = KnowledgeGraphGenerator()
        
        # Get all text chunks for this document
        query = "SELECT embedding_id, content FROM Document_Embeddings WHERE doc_id = %s"
        chunks = conn.execute_query(query, (doc_id,))
        total_chunks = len(chunks)
        
        # Process chunks and generate knowledge graph
        for chunk_num, (embedding_id, content) in enumerate(chunks, 1):
            try:
                logger.info(f"Extracting entities and relationships from chunk {embedding_id}...")
                knowledge = kg_generator.extract_knowledge_sync(content, doc_id, embedding_id)
                
                # Store entities
                for entity in knowledge['entities']:
                    query = """
                        INSERT INTO Entities (name, description, aliases, category)
                        VALUES (%s, %s, %s, %s)
                    """
                    conn.execute_query(query, (
                        entity['name'],
                        entity['description'],
                        json.dumps(entity.get('aliases', [])),
                        entity['category']
                    ))
                    logger.info(f"Stored entity: {entity['name']} ({entity['category']})")
                
                # Store relationships
                for rel in knowledge['relationships']:
                    query = """
                        INSERT INTO Relationships (doc_id, source_entity_id, target_entity_id, relation_type)
                        SELECT %s, e1.entity_id, e2.entity_id, %s
                        FROM Entities e1, Entities e2
                        WHERE e1.name = %s AND e2.name = %s
                    """
                    conn.execute_query(query, (
                        doc_id,
                        rel['relation_type'],
                        rel['source'],
                        rel['target']
                    ))
                    logger.info(f"Stored relationship: {rel['source']} -{rel['relation_type']}-> {rel['target']}")
                
                logger.info(f"Successfully processed chunk {embedding_id}")
                
                if task:
                    # Update progress (50% of total progress allocated to knowledge graph)
                    progress = 50 + int((chunk_num / total_chunks) * 50)
                    task.update_state(state='PROCESSING', meta={
                        'status': f'Analyzing document content ({chunk_num}/{total_chunks})',
                        'current': progress,
                        'total': 100
                    })
                    
            except Exception as e:
                logger.error(f"Error processing chunk {embedding_id}: {str(e)}")
                # Continue with next chunk even if one fails
                continue
        
        # Update status to completed
        update_processing_status(doc_id, "completed")
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        update_processing_status(doc_id, "failed", str(e))
        raise
    finally:
        conn.disconnect()
