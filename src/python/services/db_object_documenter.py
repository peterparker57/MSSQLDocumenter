"""Base class for database object documentation."""
import logging
import pyodbc
from typing import Dict, Any, List, Optional
from .llm_client import LLMClient
from .vector_store import VectorStore
from .sql_queries import *

logger = logging.getLogger(__name__)

class DatabaseObjectDocumenter:
    """Base class for documenting database objects."""
    
    def __init__(self, connection_string: str, schema: str, name: str, llm_client: LLMClient, vector_store: VectorStore):
        """Initialize the documenter."""
        self.connection_string = connection_string
        self.schema = schema
        self.name = name
        self.llm_client = llm_client
        self.vector_store = vector_store
        
    def _get_db_connection(self):
        """Get a database connection."""
        return pyodbc.connect(self.connection_string)
    
    def _execute_query(self, query: str, *params) -> List[Any]:
        """Execute a query and return results."""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, *params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
            
    async def _get_definition(self) -> Optional[str]:
        """Get object definition."""
        try:
            results = self._execute_query(OBJECT_DEFINITION_QUERY, self.schema, self.name)
            return results[0][0] if results else None
        except Exception as e:
            logger.error(f"Failed to get definition: {str(e)}")
            return None
            
    def _format_type_info(self, type_info: Any) -> str:
        """Format type information including length/precision/scale."""
        type_str = type_info.data_type
        if type_info.max_length != -1:
            type_str += f"({type_info.max_length})"
        elif type_info.precision:
            type_str += f"({type_info.precision}"
            if type_info.scale:
                type_str += f",{type_info.scale}"
            type_str += ")"
        return type_str
            
    def _store_documentation(self, content: str, metadata: Dict[str, Any], obj_type: str):
        """Store documentation in vector store."""
        self.vector_store.add_documentation(
            schema=self.schema,
            name=self.name,
            obj_type=obj_type,
            content=content,
            metadata=metadata
        )
        
    async def document(self) -> None:
        """Document the database object. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement document()")

    async def _get_llm_analysis(self, doc: str, obj_type: str) -> Optional[str]:
        """Get LLM analysis of the object."""
        try:
            analysis_methods = {
                "table": self.llm_client.analyze_table,
                "view": self.llm_client.analyze_view,
                "procedure": self.llm_client.analyze_procedure,
                "function": self.llm_client.analyze_function
            }
            
            if obj_type not in analysis_methods:
                logger.error(f"Unsupported object type for LLM analysis: {obj_type}")
                return None
                
            return await analysis_methods[obj_type](doc)
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}")
            return None