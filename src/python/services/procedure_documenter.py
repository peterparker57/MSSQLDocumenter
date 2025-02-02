"""Stored procedure documentation implementation."""
from typing import Dict, Any, List
import logging
from .db_object_documenter import DatabaseObjectDocumenter
from .sql_queries import PROCEDURE_PARAMS_QUERY, OBJECT_DEFINITION_QUERY

logger = logging.getLogger(__name__)

class ProcedureDocumenter(DatabaseObjectDocumenter):
    """Documents SQL Server stored procedures."""
    
    async def document(self) -> None:
        """Document a stored procedure."""
        try:
            logger.info(f"Documenting procedure {self.schema}.{self.name}")
            
            # Get parameters
            parameters = self._execute_query(
                PROCEDURE_PARAMS_QUERY,
                self.schema,
                self.name
            )
            
            # Get procedure definition
            definition = await self._get_definition()
            if not definition:
                raise ValueError(f"Could not retrieve definition for procedure {self.schema}.{self.name}")
            
            # Format documentation
            doc = f"Stored Procedure: {self.schema}.{self.name}\n"
            
            # Add parameter information
            if parameters:
                doc += "\nParameters:\n"
                for param in parameters:
                    doc += f"\n{param.param_name} ({self._format_type_info(param)})"
                    if param.is_output:
                        doc += " OUTPUT"
                    if param.description:
                        doc += f"\n  Description: {param.description}"
            
            # Add definition
            doc += f"\n\nDefinition:\n{definition}"
            
            # Get LLM analysis
            analysis = await self._get_llm_analysis(doc, "procedure")
            if analysis:
                doc += f"\n\nAnalysis:\n{analysis}"
            
            # Store documentation
            self._store_documentation(
                content=doc,
                metadata={
                    "parameter_count": len(parameters),
                    "definition_length": len(definition)
                },
                obj_type="procedure"
            )
            
        except Exception as e:
            logger.error(f"Failed to document procedure {self.schema}.{self.name}: {str(e)}")
            raise