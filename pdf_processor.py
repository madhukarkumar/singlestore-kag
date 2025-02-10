import os
import fitz  # PyMuPDF
from datetime import datetime
from typing import Optional, Tuple
from pathlib import Path
from db import get_connection
from models import ProcessingStatus

DOCUMENTS_DIR = Path("documents")
DOCUMENTS_DIR.mkdir(exist_ok=True)

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
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # Create document record
            cursor.execute(
                """
                INSERT INTO Documents (title, source)
                VALUES (%s, %s)
                """,
                (filename, file_path)
            )
            doc_id = cursor.lastrowid

            # Create processing status record
            cursor.execute(
                """
                INSERT INTO ProcessingStatus 
                (doc_id, file_name, file_path, file_size, current_step)
                VALUES (%s, %s, %s, %s, 'started')
                """,
                (doc_id, filename, file_path, file_size)
            )
            
            return doc_id

def update_processing_status(doc_id: int, step: str, error_message: Optional[str] = None):
    """Update processing status for a document"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE ProcessingStatus
                SET current_step = %s, error_message = %s
                WHERE doc_id = %s
                """,
                (step, error_message, doc_id)
            )

def get_processing_status(doc_id: int) -> dict:
    """Get current processing status"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT current_step, error_message, file_name
                FROM ProcessingStatus
                WHERE doc_id = %s
                """,
                (doc_id,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    "currentStep": result[0],
                    "errorMessage": result[1],
                    "fileName": result[2]
                }
            return None

def cleanup_processing(doc_id: int):
    """Clean up processing data for cancelled/failed jobs"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # Get file path
            cursor.execute(
                "SELECT file_path FROM ProcessingStatus WHERE doc_id = %s",
                (doc_id,)
            )
            result = cursor.fetchone()
            if result:
                file_path = result[0]
                
                # Delete document and related data (cascading delete will handle other tables)
                cursor.execute("DELETE FROM Documents WHERE doc_id = %s", (doc_id,))
                
                # Delete file if it exists
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

async def process_pdf(doc_id: int):
    """
    Process PDF file through all steps
    """
    try:
        # Get file path
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT file_path FROM ProcessingStatus WHERE doc_id = %s",
                    (doc_id,)
                )
                file_path = cursor.fetchone()[0]

        # Validate PDF
        is_valid, error = validate_pdf(file_path)
        if not is_valid:
            raise PDFProcessingError(error)

        # Create semantic chunks
        update_processing_status(doc_id, "chunking")
        # TODO: Call existing chunking function
        
        # Generate embeddings
        update_processing_status(doc_id, "embeddings")
        # TODO: Call existing embedding generation function
        
        # Extract entities
        update_processing_status(doc_id, "entities")
        # TODO: Call existing entity extraction function
        
        # Extract relationships
        update_processing_status(doc_id, "relationships")
        # TODO: Call existing relationship extraction function
        
        # Mark as completed
        update_processing_status(doc_id, "completed")
        
    except Exception as e:
        update_processing_status(doc_id, "failed", str(e))
        raise
