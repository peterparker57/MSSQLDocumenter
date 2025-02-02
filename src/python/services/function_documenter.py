"""Function documentation implementation."""
from typing import Dict, Any, List
import logging
from .db_object_documenter import DatabaseObjectDocumenter
from .sql_queries import FUNCTION_PARAMS_QUERY, FUNCTION_RETURN_TYPE_QUERY, OBJECT_DEFINITION_QUERY

logger = logging.getLogger(__name__)

class FunctionDocumenter(DatabaseObjectDocumenter):
    """Documents SQL Server functions."""
    
    async def document(self) -> None:
        """Document a function."""
        try:
            logger.info(f"Documenting function {self.schema}.{self.name}")
            
            # Get parameters
            parameters = self._execute_query(
                FUNCTION_PARAMS_QUERY,
                self.schema,
                self.name
            )
            
            # Get return type
            return_type_result = self._execute_query(
                FUNCTION_RETURN_TYPE_QUERY,
                self.schema,
                self.name
            )
            if not return_type_result:
                raise ValueError(f"Could not retrieve return type for function {self.schema}.{self.name}")
            return_type = return_type_result[0]
            
            # Get function definition
            definition = await self._get_definition()
            if not definition:
                raise ValueError(f"Could not retrieve definition for function {self.schema}.{self.name}")
            
            # Format documentation
            doc = f"Function: {self.schema}.{self.name}\n"
            
            # Add return type information
            doc += f"\nReturns: {return_type.return_type}"
            if return_type.max_length != -1:
                doc += f"({return_type.max_length})"
            elif return_type.precision:
                doc += f"({return_type.precision}"
                if return_type.scale:
                    doc += f",{return_type.scale}"
                doc += ")"
            
            # Add parameter information
            if parameters:
                doc += "\n\nParameters:\n"
                for param in parameters:
                    doc += f"\n{param.param_name} ({self._format_type_info(param)})"
                    if param.description:
                        doc += f"\n  Description: {param.description}"
            
            # Add definition
            doc += f"\n\nDefinition:\n{definition}"
            
            # Get LLM analysis
            analysis = await self._get_llm_analysis(doc, "function")
            if analysis:
                doc += f"\n\nAnalysis:\n{analysis}"
            
            # Store documentation
            self._store_documentation(
                content=doc,
                metadata={
                    "parameter_count": len(parameters),
                    "definition_length": len(definition),
                    "return_type": return_type.return_type
                },
                obj_type="function"
            )
            
        except Exception as e:
            logger.error(f"Failed to document function {self.schema}.{self.name}: {str(e)}")
            raise