from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import json
import os
from pathlib import Path
import asyncio

from ..models.request import ConnectionRequest, BatchRequest
from ..models.response import ConnectionResponse
from ..config.server import server_config
from ..utils.logging import get_logger

logger = get_logger("api.routes")

router = APIRouter()

# Get the base directory from server config
base_dir = server_config.base_dir
connection_file = base_dir / "connection.json"

@router.get("/api/status")
async def get_status():
    """Get current connection status."""
    try:
        return {
            "connected": server_config.is_documenter_initialized,
            "llm_ready": server_config.is_llm_initialized
        }
    except Exception as e:
        logger.error(f"Failed to get status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/vector-store/status")
async def get_vector_store_status():
    """Get vector store statistics."""
    try:
        if not server_config.is_documenter_initialized:
            raise HTTPException(status_code=400, detail="Documenter not initialized")
            
        stats = server_config.documenter.vector_store.get_stats()
        return {
            "status": "success",
            "tables_count": stats.get("table", 0),
            "views_count": stats.get("view", 0),
            "procedures_count": stats.get("procedure", 0),
            "functions_count": stats.get("function", 0)
        }
    except Exception as e:
        logger.error(f"Failed to get vector store stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/vector-store/clear")
async def clear_vector_store():
    """Clear all documentation from vector store."""
    try:
        if not server_config.is_documenter_initialized:
            raise HTTPException(status_code=400, detail="Documenter not initialized")
            
        server_config.documenter.clear_documentation()
        return {"status": "success", "message": "Vector store cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear vector store: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/connect")
async def connect(request: ConnectionRequest) -> ConnectionResponse:
    """Initialize database connection and save connection info."""
    try:
        logger.info(f"Initializing connection to {request.server}/{request.database}")
        
        # Build connection string
        if request.trusted_connection:
            connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={request.server};DATABASE={request.database};Trusted_Connection=yes"
        else:
            connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={request.server};DATABASE={request.database};UID={request.username};PWD={request.password}"
        
        # Save connection info
        save_connection_info(request)
        
        # Initialize documenter
        server_config.init_documenter(
            server=request.server,
            database=request.database,
            connection_string=connection_string,
            persist_directory=str(base_dir / "vector_store")
        )
        
        # Initialize LLM client
        server_config.init_llm_client()
        
        # Test connections
        result = await server_config.documenter.test_connection()
        logger.info("Connection test result:", extra={"result": result})
        return ConnectionResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to initialize documenter: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/saved-connection")
async def get_saved_connection() -> Optional[ConnectionRequest]:
    """Get saved connection information."""
    try:
        if connection_file.exists():
            with open(connection_file, 'r') as f:
                data = json.load(f)
                return ConnectionRequest(**data)
        return None
    except Exception as e:
        logger.error(f"Failed to read saved connection: {str(e)}", exc_info=True)
        return None

def save_connection_info(connection: ConnectionRequest) -> None:
    """Save connection information to file."""
    try:
        with open(connection_file, 'w') as f:
            json.dump(connection.dict(), f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save connection info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save connection info: {str(e)}")

@router.post("/api/batch")
async def process_batch(request: BatchRequest):
    """Process a batch of database objects."""
    try:
        logger.info("Received batch documentation request")
        logger.debug(f"Request parameters: {request.dict()}")

        if not server_config.is_documenter_initialized:
            logger.error("Documenter not initialized")
            raise HTTPException(status_code=400, detail="Documenter not initialized")
            
        # Prepare parameters
        object_types = request.object_types if request.object_types is not None else []
        schemas = request.schemas
        batch_size = request.batch_size if request.batch_size is not None else 50
        include_llm = request.include_llm_analysis if request.include_llm_analysis is not None else True
        
        logger.info(f"Starting documentation process with: object_types={object_types}, schemas={schemas}, batch_size={batch_size}, include_llm={include_llm}")
            
        # Start documentation process
        try:
            # Reset progress before starting
            server_config.documenter.reset_progress()
            
            # Start the documentation process in a background task
            asyncio.create_task(server_config.documenter.document_batch(
                object_types=object_types,
                schemas=schemas,
                batch_size=batch_size,
                include_llm_analysis=include_llm
            ))
            
            # Wait a moment for the process to start
            await asyncio.sleep(0.5)
            
            logger.info("Documentation process started successfully")
            return {"status": "started"}
        except Exception as batch_error:
            logger.error(f"Failed to start batch documentation: {str(batch_error)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to start documentation: {str(batch_error)}")
        
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/batch/progress")
async def get_batch_progress():
    """Get progress of the current batch documentation task."""
    try:
        logger.debug("Checking progress")

        if not server_config.is_documenter_initialized:
            logger.error("Documenter not initialized when checking progress")
            raise HTTPException(status_code=400, detail="Documenter not initialized")
            
        progress = server_config.documenter.get_progress()
        logger.debug(f"Raw progress data: {progress}")
        
        return progress
        
    except Exception as e:
        logger.error(f"Failed to get batch progress: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/search")
async def search_documentation(query: str, limit: int = 5):
    """Search documentation using natural language."""
    try:
        if not server_config.is_documenter_initialized:
            raise HTTPException(status_code=400, detail="Documenter not initialized")
            
        logger.info(f"Searching documentation with query: {query}, limit: {limit}")
        results = server_config.documenter.search_documentation(query, limit)
        logger.debug(f"Search returned {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/related/{schema}/{name}/{type}")
async def get_related_objects(schema: str, name: str, type: str):
    """Get related objects for a specific database object."""
    try:
        if not server_config.is_documenter_initialized:
            raise HTTPException(status_code=400, detail="Documenter not initialized")
            
        logger.info(f"Getting related objects for {schema}.{name} ({type})")
        results = server_config.documenter.get_related_objects(schema, name, type)
        logger.debug(f"Found {len(results)} related objects")
        return results
        
    except Exception as e:
        logger.error(f"Failed to get related objects: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/summary/{schema}/{name}/{type}")
async def get_documentation_summary(schema: str, name: str, type: str):
    """Get documentation summary for a specific object."""
    try:
        if not server_config.is_documenter_initialized:
            raise HTTPException(status_code=400, detail="Documenter not initialized")
            
        logger.info(f"Generating summary for {schema}.{name} ({type})")
        summary = server_config.documenter.generate_documentation_summary(schema, name, type)
        return {"summary": summary}
        
    except Exception as e:
        logger.error(f"Failed to generate summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))