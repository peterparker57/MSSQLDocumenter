"""Database documentation service."""
import logging
import pyodbc
from datetime import datetime
from typing import Dict, Any, List, Optional

from .db_object_documenter import DatabaseObjectDocumenter
from .table_documenter import TableDocumenter
from .view_documenter import ViewDocumenter
from .procedure_documenter import ProcedureDocumenter
from .function_documenter import FunctionDocumenter
from .llm_client import LLMClient
from .vector_store import VectorStore
from ..utils.logging import get_logger
from .sql_queries import OBJECT_QUERIES

logger = get_logger("documenter")

class DatabaseDocumenter:
    """Main database documentation service."""
    
    def __init__(self, server: str, database: str, connection_string: str, persist_directory: str):
        """Initialize the database documenter."""
        self.server = server
        self.database = database
        self.connection_string = connection_string
        self.persist_directory = persist_directory
        self.llm_client = LLMClient()
        self.vector_store = VectorStore(persist_directory)
        self.progress = {
            "current": 0,
            "total": 0,
            "current_object": "",
            "phase": "Not Started",
            "start_time": None,
            "estimated_time_remaining": None,
            "cost": 0.0,
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            }
        }
        
    def reset_progress(self):
        """Reset progress tracking."""
        self.progress = {
            "current": 0,
            "total": 0,
            "current_object": "",
            "phase": "Not Started",
            "start_time": None,
            "estimated_time_remaining": None,
            "cost": 0.0,
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            }
        }
        
    def get_progress(self) -> Dict[str, Any]:
        """Get the current documentation progress."""
        return self.progress.copy()
        
    def clear_documentation(self):
        """Clear all stored documentation."""
        self.vector_store.clear()
        self.reset_progress()
        
    async def document_batch(
        self,
        object_types: List[str],
        schemas: Optional[List[str]] = None,
        batch_size: int = 50,
        include_llm_analysis: bool = True
    ):
        """Document a batch of database objects."""
        try:
            logger.info(f"Starting batch documentation with types={object_types}, schemas={schemas}, batch_size={batch_size}")
            self.reset_progress()
            self.progress["start_time"] = datetime.now()
            self.progress["phase"] = "Initializing"
            
            # Get objects to document
            objects = await self._get_database_objects(object_types, schemas)
            self.progress["total"] = len(objects)
            self.progress["phase"] = "Processing"
            
            # Create appropriate documenters for each object
            documenters = {
                "table": TableDocumenter,
                "view": ViewDocumenter,
                "procedure": ProcedureDocumenter,
                "function": FunctionDocumenter
            }
            
            # Process in batches
            for i in range(0, len(objects), batch_size):
                batch = objects[i:i + batch_size]
                
                for obj in batch:
                    self.progress["current_object"] = f"{obj['schema_name']}.{obj['name']}"
                    
                    # Create appropriate documenter
                    if obj["type"] not in documenters:
                        logger.warning(f"Unsupported object type: {obj['type']}")
                        continue
                        
                    documenter_class = documenters[obj["type"]]
                    documenter = documenter_class(
                        connection_string=self.connection_string,
                        schema=obj["schema_name"],
                        name=obj["name"],
                        llm_client=self.llm_client,
                        vector_store=self.vector_store
                    )
                    
                    # Document the object
                    await documenter.document()
                    
                    self.progress["current"] += 1
                    
                    # Update estimated time remaining
                    if self.progress["current"] > 1:
                        elapsed_time = (datetime.now() - self.progress["start_time"]).total_seconds()
                        objects_remaining = self.progress["total"] - self.progress["current"]
                        avg_time_per_object = elapsed_time / self.progress["current"]
                        self.progress["estimated_time_remaining"] = int(objects_remaining * avg_time_per_object)
            
            self.progress["phase"] = "Complete"
            logger.info("Batch documentation completed")
            logger.info(f"Total cost: ${self.progress['cost']:.4f}")
            logger.info(f"Total tokens: {self.progress['usage']['total_tokens']}")
            
        except Exception as e:
            self.progress["phase"] = "Failed"
            logger.error(f"Batch documentation failed: {str(e)}")
            raise
            
    async def _get_database_objects(
        self,
        object_types: Optional[List[str]] = None,
        schemas: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get filtered database objects."""
        try:
            objects = []
            schema_filter = "AND s.name IN ({})".format(
                ",".join(f"'{s}'" for s in schemas)
            ) if schemas else ""
            
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                
                for obj_type in (object_types or OBJECT_QUERIES.keys()):
                    if obj_type not in OBJECT_QUERIES:
                        logger.warning(f"Unsupported object type: {obj_type}")
                        continue
                        
                    query = OBJECT_QUERIES[obj_type].format(schema_filter=schema_filter)
                    cursor.execute(query)
                    
                    objects.extend([
                        {"schema_name": row[0], "name": row[1], "type": row[2]}
                        for row in cursor.fetchall()
                    ])
                    
            return objects
            
        except Exception as e:
            logger.error(f"Error getting database objects: {str(e)}")
            raise
            
    async def test_connection(self) -> Dict[str, Any]:
        """Test both database and LLM connections."""
        try:
            # Test database connection
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT @@VERSION")
                db_version = cursor.fetchone()[0]
                logger.info("Database connection test successful")
                
                # Test LLM connection
                try:
                    llm_test = await self.llm_client.test_connection()
                    logger.info("LLM connection test successful")
                    
                    return {
                        "connected": True,
                        "database_version": db_version,
                        "llm_status": llm_test
                    }
                except Exception as llm_error:
                    logger.error(f"LLM test failed: {str(llm_error)}")
                    return {
                        "connected": True,
                        "database_version": db_version,
                        "llm_status": {"error": str(llm_error)}
                    }
                    
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "connected": False,
                "error": str(e)
            }
            
    def search_documentation(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search documentation using natural language."""
        return self.vector_store.search(query, n_results)
        
    def get_documentation_summary(self, schema: str, name: str, obj_type: str) -> str:
        """Generate a documentation summary for a specific object."""
        try:
            # Search for the object in the vector store
            results = self.vector_store.search(f"{schema}.{name} {obj_type}", n_results=1)
            if results:
                # Extract just the documentation without the LLM analysis
                doc = results[0]["content"]
                analysis_index = doc.find("\n\nAnalysis:")
                if analysis_index > -1:
                    doc = doc[:analysis_index]
                return doc
            return f"No documentation found for {obj_type} {schema}.{name}"
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
            return f"Error generating summary: {str(e)}"