"""
SingleStore database connection and operations module.
"""
import os
import logging
from typing import Optional, Any, Dict, List, Tuple

import singlestoredb as s2
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)

# Database configuration
DB_HOST = os.getenv("SINGLESTORE_HOST")
DB_PORT = os.getenv("SINGLESTORE_PORT", "3306")  # Default SingleStore port
DB_USER = os.getenv("SINGLESTORE_USER")
DB_PASSWORD = os.getenv("SINGLESTORE_PASSWORD")
DB_DATABASE = os.getenv("SINGLESTORE_DATABASE")

class DatabaseConnection:
    """Manages database connections and operations for SingleStore."""
    
    def __init__(self):
        """Initialize the database connection."""
        self.conn = None
        self.cursor = None
        
    def connect(self) -> None:
        """
        Establish connection to SingleStore database.
        Raises:
            Exception: If connection fails or required environment variables are missing.
        """
        if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE]):
            raise ValueError(
                "Missing required database configuration. Please ensure all required "
                "environment variables are set in .env file:\n"
                "- SINGLESTORE_HOST\n"
                "- SINGLESTORE_USER\n"
                "- SINGLESTORE_PASSWORD\n"
                "- SINGLESTORE_DATABASE"
            )
        
        try:
            self.conn = s2.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_DATABASE
            )
            self.cursor = self.conn.cursor()
            logger.info("Successfully connected to SingleStore database")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def disconnect(self) -> None:
        """Close database connection and cursor."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[List[Tuple[Any, ...]]]:
        """
        Execute a SQL query and return results if any.
        
        Args:
            query: SQL query to execute
            params: Optional tuple of parameters for the query
            
        Returns:
            List of tuples containing the query results, or None for non-SELECT queries
            
        Raises:
            Exception: If query execution fails
        """
        try:
            if not self.conn or getattr(self.conn, '_closed', True):
                logger.error("No active database connection")
                raise Exception("No active database connection")
            
            if not self.cursor:
                self.cursor = self.conn.cursor()
            
            self.cursor.execute(query, params)
            
            # For SELECT queries, return results
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            
            # For non-SELECT queries, commit the transaction
            self.conn.commit()
            return None
            
        except Exception as e:
            logger.error("Query execution failed: %s", str(e))
            if self.conn:
                self.conn.rollback()
            raise
    
    def is_connected(self) -> bool:
        """Check if the database connection is open and valid."""
        if self.conn is None or self.cursor is None:
            return False
        try:
            # Check if connection is open
            if getattr(self.conn, '_closed', True):
                return False
            # Test connection with a simple query
            self.cursor.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

def test_connection() -> None:
    """
    Test the database connection and run a simple query.
    This function will:
    1. Try to establish a connection
    2. Run a simple SELECT query to verify query execution
    3. Print the database version and current time
    """
    try:
        with DatabaseConnection() as db:
            # Test connection status
            is_connected = db.is_connected()
            print(f"Connection Status: {'✅ Connected' if is_connected else '❌ Not Connected'}")
            
            # Test basic connection and version
            version = db.execute_query("SELECT VERSION()")
            if version:
                print(f"✅ Successfully connected to SingleStore!")
                print(f"Database Version: {version[0][0]}")
            
            # Test query execution with current timestamp
            time_result = db.execute_query("SELECT NOW()")
            if time_result:
                print(f"Current Database Time: {time_result[0][0]}")
            
            # Test current user and database info - fixed syntax
            user_info = db.execute_query("""
                SELECT USER() AS user, DATABASE() AS db
            """)
            if user_info:
                print(f"Connected User: {user_info[0][0]}")
                print(f"Current Database: {user_info[0][1]}")
                
            print("\n✅ All connection tests passed successfully!")
            
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the connection test
    test_connection()
