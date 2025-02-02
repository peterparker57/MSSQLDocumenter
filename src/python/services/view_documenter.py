"""View documentation implementation."""
from typing import Dict, Any, List
import logging
from .db_object_documenter import DatabaseObjectDocumenter
from .sql_queries import VIEW_COLUMNS_QUERY, OBJECT_DEFINITION_QUERY

logger = logging.getLogger(__name__)

class ViewDocumenter(DatabaseObjectDocumenter):
    """Documents SQL Server views."""
    
    async def document(self) -> None:
        """Document a view."""
        try:
            logger.info(f"Documenting view {self.schema}.{self.name}")
            
            # Get columns
            columns = self._execute_query(VIEW_COLUMNS_QUERY, self.schema, self.name)
            
            # Get view definition
            definition = await self._get_definition()
            if not definition:
                raise ValueError(f"Could not retrieve definition for view {self.schema}.{self.name}")
            
            # Format documentation
            doc = f"View: {self.schema}.{self.name}\n\nColumns:\n"
            
            # Add column information
            for col in columns:
                doc += f"\n{col.column_name} ({self._format_type_info(col)})"
                if not col.is_nullable:
                    doc += " NOT NULL"
                if col.description:
                    doc += f"\n  Description: {col.description}"
            
            # Add definition
            doc += f"\n\nDefinition:\n{definition}"
            
            # Get LLM analysis
            analysis = await self._get_llm_analysis(doc, "view")
            if analysis:
                doc += f"\n\nAnalysis:\n{analysis}"
            
            # Store documentation
            self._store_documentation(
                content=doc,
                metadata={
                    "column_count": len(columns),
                    "definition_length": len(definition)
                },
                obj_type="view"
            )
            
        except Exception as e:
            logger.error(f"Failed to document view {self.schema}.{self.name}: {str(e)}")
            raise