from main import DocumentProcessor

processor = DocumentProcessor()
results = processor.process_document("document.pdf", document_id=1)#!/usr/bin/env python3
import os
import sys
import logging
from db import DatabaseConnection
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def run_command(cmd):
    """Run a command and log its output."""
    logger.info("Running command: %s", " ".join(cmd))
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Command failed with error: %s", e.stderr)
        return False

def check_database_setup(db):
    """Check database setup and required tables."""
    required_tables = {
        "document_embeddings": False,
        "knowledge_graph": False
    }
    
    for table in required_tables:
        exists = db.table_exists(table)
        required_tables[table] = exists
        logger.info("Table '%s': %s", table, "✅ exists" if exists else "❌ missing")
    
    return required_tables

def main():
    try:
        # Step 1: Check database setup
        logger.info("Step 1: Checking database setup...")
        with DatabaseConnection() as db:
            tables = check_database_setup(db)
            
            # Create knowledge_graph table if it doesn't exist
            if not tables["knowledge_graph"]:
                logger.info("Creating knowledge_graph table...")
                db.create_knowledge_graph_table()
            
            # Verify document_embeddings table exists
            if not tables["document_embeddings"]:
                logger.error("document_embeddings table is missing. Please create it first.")
                sys.exit(1)
        
        # Step 2: Process markdown file and create embeddings
        logger.info("\nStep 2: Processing markdown file and creating embeddings...")
        markdown_file = sys.argv[1] if len(sys.argv) > 1 else None
        document_id = sys.argv[2] if len(sys.argv) > 2 else "1"
        
        if not markdown_file:
            logger.error("Please provide the path to your markdown file as argument")
            sys.exit(1)
            
        if not os.path.exists(markdown_file):
            logger.error("Markdown file not found: %s", markdown_file)
            sys.exit(1)
            
        # Create embeddings using main.py
        success = run_command([
            "python", "main.py",
            "--markdown", markdown_file,
            "--document_id", document_id
        ])
        
        if not success:
            logger.error("Failed to create embeddings")
            sys.exit(1)
            
        # Step 3: Create knowledge graph from embeddings
        logger.info("\nStep 3: Creating knowledge graph from embeddings...")
        success = run_command(["python", "create_knowledge_from_table.py"])
        
        if not success:
            logger.error("Failed to create knowledge graph")
            sys.exit(1)
            
        logger.info("\n✅ Workflow completed successfully!")
        
        # Step 4: Show some statistics
        with DatabaseConnection() as db:
            # Count embeddings
            embeddings_count = db.execute_query(
                "SELECT COUNT(*) FROM document_embeddings WHERE document_id = %s",
                (document_id,)
            )
            # Count knowledge graph entries
            knowledge_count = db.execute_query(
                "SELECT COUNT(*) FROM knowledge_graph"
            )
            
            logger.info("\nStatistics:")
            logger.info("- Document embeddings created: %d", embeddings_count[0][0])
            logger.info("- Knowledge graph entries created: %d", knowledge_count[0][0])
            
    except Exception as e:
        logger.error("Workflow failed: %s", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
