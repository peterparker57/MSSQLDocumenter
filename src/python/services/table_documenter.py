"""Table documentation implementation."""
from typing import Dict, Any, List
import logging
from .db_object_documenter import DatabaseObjectDocumenter
from .sql_queries import TABLE_COLUMNS_QUERY, INDEXES_QUERY, FOREIGN_KEYS_QUERY

logger = logging.getLogger(__name__)

class TableDocumenter(DatabaseObjectDocumenter):
    """Documents SQL Server tables."""
    
    async def document(self) -> None:
        """Document a table."""
        try:
            logger.info(f"Documenting table {self.schema}.{self.name}")
            
            # Get columns
            columns = self._execute_query(TABLE_COLUMNS_QUERY, self.schema, self.name)
            
            # Get indexes
            indexes = self._execute_query(INDEXES_QUERY, self.schema, self.name)
            
            # Get foreign keys
            foreign_keys = self._execute_query(FOREIGN_KEYS_QUERY, self.schema, self.name)
            
            # Format documentation
            doc = f"Table: {self.schema}.{self.name}\n\nColumns:\n"
            
            # Add column information
            for col in columns:
                doc += f"\n{col.column_name} ({self._format_type_info(col)})"
                if not col.is_nullable:
                    doc += " NOT NULL"
                if col.description:
                    doc += f"\n  Description: {col.description}"
            
            # Add index information
            if indexes:
                doc += "\n\nIndexes:\n"
                for idx in indexes:
                    doc += f"\n{idx.index_name} ({idx.type_desc})"
                    if idx.is_unique:
                        doc += " UNIQUE"
                    doc += f"\n  Columns: {idx.columns}"
            
            # Add foreign key information
            if foreign_keys:
                doc += "\n\nForeign Keys:\n"
                for fk in foreign_keys:
                    doc += f"\n{fk.fk_name}"
                    doc += f"\n  References: {fk.referenced_schema}.{fk.referenced_table}"
                    doc += f"\n  Columns: {fk.columns} -> {fk.referenced_columns}"
            
            # Get LLM analysis
            analysis = await self._get_llm_analysis(doc, "table")
            if analysis:
                doc += f"\n\nAnalysis:\n{analysis}"
            
            # Store documentation
            self._store_documentation(
                content=doc,
                metadata={
                    "column_count": len(columns),
                    "has_indexes": bool(indexes),
                    "has_foreign_keys": bool(foreign_keys)
                },
                obj_type="table"
            )
            
        except Exception as e:
            logger.error(f"Failed to document table {self.schema}.{self.name}: {str(e)}")
            raise